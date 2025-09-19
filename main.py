import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import create_db_and_tables, get_db, SessionLocal
import spotify
import crud
import models
import datetime

# This will be loaded from Replit's Secrets
CRON_SECRET = os.getenv("CRON_SECRET")

app = FastAPI()

# This is a one-time startup event, not a background task manager.
# Replit will run this when the application boots.
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/tasks/update-playing")
def update_playing_task(x_cron_secret: str = Header(None), db: Session = Depends(get_db)):
    if not CRON_SECRET or x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized.")

    active_shares = crud.get_active_shares(db)
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
                    token.refresh_token, new_token_data["expires_at"]
                )
                token.access_token = new_token_data["access_token"]
            except Exception:
                crud.stop_sharing(db, user.id)
                continue

        currently_playing = spotify.get_currently_playing(token.access_token)
        if currently_playing and currently_playing["is_playing"]:
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

    return {"message": "Track update task completed."}

@app.get("/auth/login")
def auth_login():
    return RedirectResponse(spotify.get_auth_url())

@app.get("/auth/callback")
def auth_callback(code: str, db: Session = Depends(get_db)):
    try:
        token_data = spotify.get_token_data_from_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not retrieve token from Spotify.") from e

    user_profile = spotify.get_user_profile(token_data["access_token"])

    user = crud.get_user_by_spotify_id(db, spotify_id=user_profile["id"])
    if not user:
        user = crud.create_user(
            db=db,
            spotify_id=user_profile["id"],
            display_name=user_profile["display_name"],
            profile_pic_url=user_profile["images"][0]["url"] if user_profile["images"] else None,
        )

    crud.create_or_update_token(
        db=db,
        user_id=user.id,
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        expires_at=token_data["expires_at"],
    )

    return {"message": "Successfully authenticated."}

@app.post("/share/start")
def share_start(share_request: models.ShareRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_spotify_id(db, spotify_id=share_request.spotify_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    crud.start_sharing(db=db, user_id=user.id)
    return {"message": "Sharing started."}

@app.post("/share/stop")
def share_stop(share_request: models.ShareRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_spotify_id(db, spotify_id=share_request.spotify_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    crud.stop_sharing(db=db, user_id=user.id)
    return {"message": "Sharing stopped."}

@app.get("/feed", response_model=list[models.TrackFeedItem])
def feed(db: Session = Depends(get_db)):
    return crud.get_feed(db=db)
