import os
import time
import datetime
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks, Request
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
import crud
import models
import spotify
from database import get_db

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

CRON_SECRET = os.getenv("CRON_SECRET")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") # For simple admin protection

app = FastAPI()

# --- Dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # We don't have a token URL, this is just for dependency usage

def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """A dependency to get the current user based on an access token."""
    db_token = db.query(models.Token).filter(models.Token.access_token == token).first()
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return db_token.user

def require_admin(current_user: models.User = Depends(get_current_user_from_token)):
    """A dependency that requires the current user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# --- Pydantic Models for Admin ---
class SettingUpdate(BaseModel):
    value: str

# --- Authentication Flow ---

@app.get("/auth/login", summary="Display login page")
def login_page():
    return FileResponse('public/login.html')

@app.get("/auth/spotify", summary="Redirect to Spotify for authorization")
def auth_spotify_redirect():
    return RedirectResponse(spotify.get_auth_url())

@app.get("/auth/callback", summary="Callback endpoint for Spotify OAuth")
def auth_callback(code: str, db: Session = Depends(get_db)):
    try:
        token_data = spotify.get_token_data_from_code(code)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with Spotify for token exchange: {e}")

    user_profile = spotify.get_user_profile(token_data["access_token"])
    user = crud.get_user_by_spotify_id(db, spotify_id=user_profile["id"])
    if not user:
        user = crud.create_user(db, spotify_id=user_profile["id"], display_name=user_profile.get("display_name"), profile_pic_url=user_profile.get("images", [{}])[0].get("url") if user_profile.get("images") else None)

    crud.create_or_update_token(db, user_id=user.id, access_token=token_data["access_token"], refresh_token=token_data["refresh_token"], expires_at=token_data["expires_at"])

    return {
        "message": "SUCCESS: Tokens retrieved. You can now use the access token for authenticated requests.",
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
    }

# --- Admin Panel API ---

@app.get("/admin/settings", summary="Get all settings (Admin Only)")
def get_all_settings(db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    settings = db.query(models.Settings).all()
    return {s.key: s.value for s in settings}

@app.post("/admin/settings/{key}", summary="Update a setting (Admin Only)")
def update_setting(key: str, setting_update: SettingUpdate, db: Session = Depends(get_db), admin: models.User = Depends(require_admin)):
    db_setting = crud.set_setting(db, key, setting_update.value)
    return {"message": f"Setting '{key}' updated successfully.", "key": db_setting.key, "value": db_setting.value}

# --- Background Task ---

async def trigger_next_batch(url: str, headers: dict, params: dict):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, headers=headers, params=params, timeout=5)
        except httpx.RequestError as e:
            print(f"Error triggering next batch: {e}")

@app.post("/tasks/update-playing", summary="Update playing status for all users")
async def update_playing_task(request: Request, background_tasks: BackgroundTasks, x_cron_secret: str = Header(None), db: Session = Depends(get_db), offset: int = 0, limit: int = 20):
    if not CRON_SECRET or x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized cron job.")

    active_shares = db.query(models.ActiveShare).offset(offset).limit(limit).all()
    if not active_shares:
        return {"message": "No more active users to process."}

    for share in active_shares:
        user = share.user
        token = crud.get_token_by_user_id(db, user.id)
        if not token:
            continue

        if token.expires_at < datetime.datetime.utcnow():
            try:
                new_token_data = spotify.refresh_access_token(token.refresh_token)
                crud.create_or_update_token(
                    db, user.id, new_token_data["access_token"],
                    new_token_data.get("refresh_token", token.refresh_token),
                    new_token_data["expires_at"]
                )
                token.access_token = new_token_data["access_token"]
            except Exception:
                crud.stop_sharing(db, user.id)
                continue

        try:
            currently_playing = spotify.get_currently_playing(token.access_token)
            if currently_playing and currently_playing.get("is_playing"):
                track_data = {
                    "track_name": currently_playing["item"]["name"],
                    "artist_name": ", ".join(artist["name"] for artist in currently_playing["item"]["artists"]),
                    "album_cover_url": currently_playing["item"]["album"]["images"][0]["url"],
                    "spotify_track_url": currently_playing["item"]["external_urls"]["spotify"],
                    "currently_playing": True,
                }
            else:
                track_data = { "track_name": "Not currently playing", "artist_name": "", "album_cover_url": "", "spotify_track_url": "", "currently_playing": False }
            crud.create_or_update_track(db, user.id, track_data)
        except Exception:
            continue

    if len(active_shares) == limit:
        next_offset = offset + limit
        next_url = str(request.url)
        headers = {'x-cron-secret': x_cron_secret}
        params = {'offset': next_offset, 'limit': limit}
        background_tasks.add_task(trigger_next_batch, next_url, headers, params)

    return {"message": f"Processed batch of {len(active_shares)} users from offset {offset}."}

# --- Public Endpoints ---

@app.get("/", summary="API Root")
def read_root():
    return {"message": "Spotify Track Sharer API is running."}

@app.get("/feed", response_model=list[models.TrackFeedItem])
def feed(db: Session = Depends(get_db)):
    """Returns the feed of currently playing tracks for all active users."""
    feed_public_setting = crud.get_setting(db, 'feed_is_public')
    if not feed_public_setting or feed_public_setting.value.lower() != 'true':
        raise HTTPException(status_code=403, detail="The feed is currently not public.")
    return crud.get_feed(db=db)

@app.post("/share/start", status_code=200, summary="Start sharing playing status")
def share_start(share_request: models.ShareRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_spotify_id(db, spotify_id=share_request.spotify_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    crud.start_sharing(db=db, user_id=user.id)
    return {"message": "Sharing started successfully."}

@app.post("/share/stop", status_code=200, summary="Stop sharing playing status")
def share_stop(share_request: models.ShareRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_spotify_id(db, spotify_id=share_request.spotify_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    crud.stop_sharing(db=db, user_id=user.id)
    return {"message": "Sharing stopped successfully."}
