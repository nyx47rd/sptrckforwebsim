import os
import time
import datetime
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks, Request
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
import crud
import models
import spotify
from database import create_db_and_tables, get_db

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

CRON_SECRET = os.getenv("CRON_SECRET")

app = FastAPI()


# --- Authentication Flow ---

@app.get("/auth/login", summary="Display login page")
def login_page():
    """
    Serves the HTML page with the 'Login with Spotify' button.
    """
    return FileResponse('public/login.html')

@app.get("/auth/spotify", summary="Redirect to Spotify for authorization")
def auth_spotify_redirect():
    """Redirects the user to Spotify's authorization page."""
    return RedirectResponse(spotify.get_auth_url())

@app.get("/auth/callback", summary="Callback endpoint for Spotify OAuth")
def auth_callback(code: str, db: Session = Depends(get_db)):
    """
    Callback endpoint for Spotify's OAuth flow.
    Exchanges the authorization code for tokens, saves user data, and returns the tokens.
    Includes detailed error handling to diagnose issues during the process.
    """
    # Step 1: Exchange authorization code for tokens
    try:
        token_data = spotify.get_token_data_from_code(code)
        if "access_token" not in token_data or "refresh_token" not in token_data:
            raise HTTPException(status_code=500, detail="Failed to retrieve valid tokens from Spotify.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with Spotify for token exchange: {e}")

    # Step 2: Get user profile from Spotify
    try:
        user_profile = spotify.get_user_profile(token_data["access_token"])
        if "id" not in user_profile:
            raise HTTPException(status_code=500, detail="Failed to retrieve user profile from Spotify.")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error communicating with Spotify for profile fetch: {e}")

    # Step 3: Get or create user in our database
    try:
        user = crud.get_user_by_spotify_id(db, spotify_id=user_profile["id"])
        if not user:
            user = crud.create_user(
                db=db,
                spotify_id=user_profile["id"],
                display_name=user_profile.get("display_name", "N/A"),
                profile_pic_url=user_profile.get("images", [{}])[0].get("url") if user_profile.get("images") else None,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error when getting or creating user: {e}")

    # Step 4: Save the tokens to our database
    try:
        crud.create_or_update_token(
            db=db,
            user_id=user.id,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_at=token_data["expires_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error when saving tokens: {e}")

    # Step 5: Return the tokens to the user
    return {
        "message": "SUCCESS: Tokens retrieved. Copy the refresh_token and add it to your Vercel Environment Variables as MY_SPOTIFY_REFRESH_TOKEN.",
        "access_token": token_data["access_token"],
        "refresh_token": token_data["refresh_token"],
        "spotify_user_id": user_profile["id"],
    }

# --- Background Task ---

async def trigger_next_batch(url: str, headers: dict, params: dict):
    """Asynchronously triggers the next batch of the cron job."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, headers=headers, params=params, timeout=5)
        except httpx.RequestError as e:
            print(f"Error triggering next batch: {e}")

@app.post("/tasks/update-playing", summary="Update playing status for all users")
async def update_playing_task(
    request: Request,
    background_tasks: BackgroundTasks,
    x_cron_secret: str = Header(None),
    db: Session = Depends(get_db),
    offset: int = 0,
    limit: int = 20
):
    """
    A background task endpoint that processes users in batches to avoid serverless timeouts.
    """
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

# --- Other Endpoints ---

@app.get("/", summary="API Root")
def read_root():
    return {"message": "Spotify Track Sharer API is running."}

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
