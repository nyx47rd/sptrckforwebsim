import os
import datetime
import base64
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# --- .ENV LOADING ---
load_dotenv()

# --- SPOTIFY SETUP ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
# The user's refresh token, stored securely as an environment variable
MY_SPOTIFY_REFRESH_TOKEN = os.getenv("MY_SPOTIFY_REFRESH_TOKEN")

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

# --- IN-MEMORY CACHE ---
cached_access_token = None
token_expiry_time = None
cached_spotify_data = None
data_cache_time = None

# --- SPOTIFY HELPER FUNCTIONS ---

def spotify_refresh_access_token():
    """
    Refreshes the access token using the long-lived refresh token,
    or returns a cached token if it's still valid.
    """
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
    access_token = token_data["access_token"]
    expires_in = token_data.get("expires_in", 3600)

    cached_access_token = access_token
    token_expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in - 60)

    return access_token

def spotify_get_currently_playing(access_token: str):
    """
    Fetches the currently playing track using a valid access token.
    """
    response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/player/currently-playing",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code == 204:
        return None
    response.raise_for_status()
    return response.json()

# --- PYDANTIC SCHEMA ---
class NowPlayingResponse(BaseModel):
    current_track: str
    album_cover: str | None
    spotify_link: str | None
    currently_playing: bool

# --- FASTAPI APP ---
app = FastAPI()

# Configure CORS
origins = [
    "https://websim.com",
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
def handle_root():
    return {"message": "Personal Now Listening API"}

@app.get("/api/now-playing", response_model=NowPlayingResponse)
def now_playing():
    global cached_spotify_data, data_cache_time

    CACHE_DURATION = datetime.timedelta(seconds=3)
    if cached_spotify_data and data_cache_time and (datetime.datetime.utcnow() - data_cache_time) < CACHE_DURATION:
        return cached_spotify_data

    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, MY_SPOTIFY_REFRESH_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Server is not configured. Missing Spotify credentials."
        )

    try:
        access_token = spotify_refresh_access_token()
        currently_playing_data = spotify_get_currently_playing(access_token)

        if currently_playing_data and currently_playing_data.get("is_playing"):
            item = currently_playing_data.get("item", {})
            if not item:
                response_data = NowPlayingResponse(
                    current_track="Playing something not exposed by API",
                    album_cover=None, spotify_link=None, currently_playing=True
                )
            else:
                track_name = item.get("name", "Unknown Track")
                artist_name = ", ".join(artist.get("name") for artist in item.get("artists", []))
                album_cover_url = item.get("album", {}).get("images", [{}])[0].get("url")
                spotify_track_url = item.get("external_urls", {}).get("spotify")

                response_data = NowPlayingResponse(
                    current_track=f"{track_name} by {artist_name}",
                    album_cover=album_cover_url,
                    spotify_link=spotify_track_url,
                    currently_playing=True,
                )
        else:
            response_data = NowPlayingResponse(
                current_track="Not currently listening",
                album_cover=None,
                spotify_link=None,
                currently_playing=False,
            )

        cached_spotify_data = response_data
        data_cache_time = datetime.datetime.utcnow()

        return response_data
    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error fetching data from Spotify. The token might be invalid. Details: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected server error occurred: {e}"
        )
