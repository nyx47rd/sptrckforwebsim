import os
import datetime
import base64
import requests
import asyncio
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# --- .ENV LOADING ---
load_dotenv()

# --- SPOTIFY SETUP ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
MY_SPOTIFY_REFRESH_TOKEN = os.getenv("MY_SPOTIFY_REFRESH_TOKEN")

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

# --- IN-MEMORY CACHE & STATE ---
cached_access_token = None
token_expiry_time = None
last_known_data = None

# --- SPOTIFY HELPER FUNCTIONS ---
def spotify_refresh_access_token():
    global cached_access_token, token_expiry_time
    if cached_access_token and token_expiry_time and datetime.datetime.utcnow() < token_expiry_time:
        return cached_access_token
    if not MY_SPOTIFY_REFRESH_TOKEN:
        raise ValueError("MY_SPOTIFY_REFRESH_TOKEN is not set in environment.")
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("ascii")).decode("ascii")
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {auth_header}"},
        data={"grant_type": "refresh_token", "refresh_token": MY_SPOTIFY_REFRESH_TOKEN},
    )
    response.raise_for_status()
    token_data = response.json()
    cached_access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 3600)
    token_expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in - 60)
    return cached_access_token

def spotify_get_currently_playing(access_token: str):
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/me/player/currently-playing", headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    if response.status_code == 204: return None
    response.raise_for_status()
    return response.json()

# --- PYDANTIC SCHEMA ---
class NowPlayingResponse(BaseModel):
    current_track: str
    album_cover: str | None
    spotify_link: str | None
    currently_playing: bool
    progress_ms: int | None
    duration_ms: int | None

# --- FASTAPI APP ---
app = FastAPI()
origins = ["https://websim.com", "http://localhost", "http://localhost:3000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def get_now_playing_data():
    """Synchronous helper to fetch and process Spotify data into our Pydantic model."""
    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, MY_SPOTIFY_REFRESH_TOKEN]):
        # This case should ideally not be hit if the endpoint check is done first.
        raise HTTPException(status_code=500, detail="Server is not configured. Contact site owner.")

    access_token = spotify_refresh_access_token()
    currently_playing_data = spotify_get_currently_playing(access_token)

    if currently_playing_data and currently_playing_data.get("is_playing"):
        item = currently_playing_data.get("item", {})
        response_data = NowPlayingResponse(
            current_track=f"{item.get('name', 'Unknown Track')} by {', '.join(artist.get('name') for artist in item.get('artists', []))}",
            album_cover=item.get("album", {}).get("images", [{}])[0].get("url") if item else None,
            spotify_link=item.get("external_urls", {}).get("spotify") if item else None,
            currently_playing=True,
            progress_ms=currently_playing_data.get("progress_ms"),
            duration_ms=item.get("duration_ms") if item else None,
        )
    else:
        response_data = NowPlayingResponse(
            current_track="Not currently listening", album_cover=None,
            spotify_link=None, currently_playing=False,
            progress_ms=None, duration_ms=None,
        )
    return response_data

@app.get("/api")
def handle_root():
    return {"message": "Personal Now Listening API"}

@app.get("/api/now-playing", response_model=NowPlayingResponse)
async def long_poll_now_playing():
    global last_known_data

    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, MY_SPOTIFY_REFRESH_TOKEN]):
        raise HTTPException(status_code=500, detail="Server is not configured. Contact site owner.")

    # Initialize state if it's the first ever request
    if last_known_data is None:
        last_known_data = get_now_playing_data()

    # Vercel's free tier timeout is 10s. We'll poll for 9s to be safe.
    timeout = 9.0
    poll_interval = 2.0
    start_time = time.time()

    while time.time() - start_time < timeout:
        current_data = get_now_playing_data()

        # Compare with the last known data sent to ANY client
        if current_data != last_known_data:
            last_known_data = current_data
            return current_data

        await asyncio.sleep(poll_interval)

    # If timeout is reached without changes, return the a.
    # This ensures the client gets a response and can immediately poll again.
    return last_known_data