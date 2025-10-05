import os
import datetime
import base64
import httpx
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# --- .ENV LOADING ---
load_dotenv()

# --- SPOTIFY SETUP ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
MY_SPOTIFY_REFRESH_TOKEN = os.getenv("MY_SPOTIFY_REFRESH_TOKEN")

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

# --- SPOTIFY HELPER FUNCTIONS ---
async def spotify_refresh_access_token():
    if not MY_SPOTIFY_REFRESH_TOKEN:
        raise ValueError("MY_SPOTIFY_REFRESH_TOKEN is not set in environment.")

    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("ascii")).decode("ascii")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            headers={"Authorization": f"Basic {auth_header}"},
            data={"grant_type": "refresh_token", "refresh_token": MY_SPOTIFY_REFRESH_TOKEN},
        )
        response.raise_for_status()
        token_data = response.json()

    return token_data["access_token"]

async def spotify_get_currently_playing(access_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
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
    progress_ms: int | None
    duration_ms: int | None

# --- FASTAPI APP ---
app = FastAPI()
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/now-playing", response_model=NowPlayingResponse)
async def now_playing():
    headers = {"Cache-Control": "public, max-age=15, s-maxage=15"}

    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, MY_SPOTIFY_REFRESH_TOKEN]):
        raise HTTPException(
            status_code=503,
            detail={"error": "server_misconfigured", "message": "Server is not configured. Contact site owner."}
        )

    try:
        access_token = await spotify_refresh_access_token()
        currently_playing_data = await spotify_get_currently_playing(access_token)

        if currently_playing_data and currently_playing_data.get("is_playing"):
            item = currently_playing_data.get("item", {})
            if not item:
                content = NowPlayingResponse(
                    current_track="Playing something not exposed by API",
                    album_cover=None, spotify_link=None, currently_playing=True,
                    progress_ms=None, duration_ms=None,
                )
            else:
                content = NowPlayingResponse(
                    current_track=f"{item.get('name', 'Unknown Track')} by {', '.join(artist.get('name') for artist in item.get('artists', []))}",
                    album_cover=item.get("album", {}).get("images", [{}])[0].get("url"),
                    spotify_link=item.get("external_urls", {}).get("spotify"),
                    currently_playing=True,
                    progress_ms=currently_playing_data.get("progress_ms"),
                    duration_ms=item.get("duration_ms"),
                )
        else:
            content = NowPlayingResponse(
                current_track="Not currently listening", album_cover=None,
                spotify_link=None, currently_playing=False,
                progress_ms=None, duration_ms=None,
            )

        return JSONResponse(content=content.model_dump(), headers=headers)

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail={"error": "spotify_api_error", "message": f"Error fetching data from Spotify: {e}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "internal_server_error", "message": f"An unexpected error occurred: {e}"})

# This handler is the entry point for Netlify's serverless function.
handler = Mangum(app)