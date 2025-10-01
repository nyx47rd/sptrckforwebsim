import os
import datetime
import base64
import requests
import asyncio
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
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

# --- IN-MEMORY CACHE (Not effective in serverless, but good practice for local dev) ---
cached_access_token = None
token_expiry_time = None

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
    response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/player/currently-playing",
        headers={"Authorization": f"Bearer {access_token}"},
    )
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
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

async def now_playing_stream_generator(request: Request):
    last_payload = None
    # Netlify's background function timeout is 15min. We run for ~14m 50s.
    stream_duration = 890
    start_time = datetime.datetime.now()

    if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, MY_SPOTIFY_REFRESH_TOKEN]):
        error_message = {
            "error": "server_misconfigured",
            "message": "Sunucu yapılandırılmamış. Site sahibiyle iletişime geçin."
        }
        yield f"data: {json.dumps(error_message)}\n\n"
        return

    while (datetime.datetime.now() - start_time).total_seconds() < stream_duration:
        if await request.is_disconnected():
            break

        try:
            access_token = spotify_refresh_access_token()
            currently_playing_data = spotify_get_currently_playing(access_token)

            if currently_playing_data and currently_playing_data.get("is_playing"):
                item = currently_playing_data.get("item", {})
                if not item:
                    response_data = NowPlayingResponse(
                        current_track="API tarafından gösterilmeyen bir içerik oynatılıyor",
                        album_cover=None, spotify_link=None, currently_playing=True,
                        progress_ms=None, duration_ms=None,
                    )
                else:
                    response_data = NowPlayingResponse(
                        current_track=f"{item.get('name', 'Bilinmeyen Şarkı')} by {', '.join(artist.get('name') for artist in item.get('artists', []))}",
                        album_cover=item.get("album", {}).get("images", [{}])[0].get("url"),
                        spotify_link=item.get("external_urls", {}).get("spotify"),
                        currently_playing=True,
                        progress_ms=currently_playing_data.get("progress_ms"),
                        duration_ms=item.get("duration_ms"),
                    )
            else:
                response_data = NowPlayingResponse(
                    current_track="Şu anda bir şey dinlemiyor", album_cover=None,
                    spotify_link=None, currently_playing=False,
                    progress_ms=None, duration_ms=None,
                )

            current_payload = response_data.model_dump_json()
            if current_payload != last_payload:
                yield f"data: {current_payload}\n\n"
                last_payload = current_payload

        except Exception as e:
            error_message = { "error": "streaming_error", "message": f"Veri akışında bir hata oluştu: {str(e)}" }
            yield f"data: {json.dumps(error_message)}\n\n"
            # We break the loop on error to allow the client to reconnect
            break

        await asyncio.sleep(2)

@app.get("/api/now-playing")
async def now_playing_sse(request: Request):
    return StreamingResponse(now_playing_stream_generator(request), media_type="text/event-stream")