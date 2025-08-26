import os
import datetime
import base64
from urllib.parse import urlencode
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

# --- SPOTIFY HELPER FUNCTIONS ---

def spotify_refresh_access_token():
    """
    Refreshes the access token using the long-lived refresh token.
    This is the only token function we need now.
    """
    if not MY_SPOTIFY_REFRESH_TOKEN:
        raise ValueError("MY_SPOTIFY_REFRESH_TOKEN is not set in environment.")

    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("ascii")).decode("ascii")
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {auth_header}"},
        data={"grant_type": "refresh_token", "refresh_token": MY_SPOTIFY_REFRESH_TOKEN},
    )
    response.raise_for_status()
    return response.json()["access_token"]

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
    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, MY_SPOTIFY_REFRESH_TOKEN]):
        raise HTTPException(
            status_code=500,
            detail="Server is not configured. Missing Spotify credentials."
        )

    try:
        # Get a fresh access token on every request for simplicity and statelessness
        access_token = spotify_refresh_access_token()

        # Fetch currently playing track
        currently_playing_data = spotify_get_currently_playing(access_token)

        if currently_playing_data and currently_playing_data.get("is_playing"):
            item = currently_playing_data.get("item", {})
            if not item:
                return NowPlayingResponse(
                    current_track="Playing something not exposed by API",
                    album_cover=None, spotify_link=None, currently_playing=True
                )

            track_name = item.get("name", "Unknown Track")
            artist_name = ", ".join(artist.get("name") for artist in item.get("artists", []))
            album_cover_url = item.get("album", {}).get("images", [{}])[0].get("url")
            spotify_track_url = item.get("external_urls", {}).get("spotify")

            return NowPlayingResponse(
                current_track=f"{track_name} by {artist_name}",
                album_cover=album_cover_url,
                spotify_link=spotify_track_url,
                currently_playing=True,
            )
        else:
            return NowPlayingResponse(
                current_track="Not currently listening",
                album_cover=None,
                spotify_link=None,
                currently_playing=False,
            )
    except requests.exceptions.HTTPError as e:
        # This can happen if the refresh token is revoked by the user
        raise HTTPException(
            status_code=400,
            detail=f"Error fetching data from Spotify. The token might be invalid. Details: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected server error occurred: {e}"
        )
