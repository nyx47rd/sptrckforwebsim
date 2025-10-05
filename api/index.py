import os
import datetime
import base64
import requests
import asyncio
import json
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# --- .ENV LOADING ---
load_dotenv()

# --- LAST.FM SETUP ---
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
LASTFM_API_BASE_URL = "https://ws.audioscrobbler.com/2.0/"

# --- LAST.FM HELPER FUNCTION ---
def get_lastfm_recent_tracks():
    params = {
        "method": "user.getrecenttracks",
        "user": LASTFM_USERNAME,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": 1
    }
    response = requests.get(LASTFM_API_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

# --- PYDANTIC SCHEMA ---
class NowPlayingResponse(BaseModel):
    track: str
    artist: str
    album_cover: str | None
    track_link: str | None
    currently_playing: bool

# --- FASTAPI APP ---
app = FastAPI()
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/now-playing", response_model=NowPlayingResponse)
async def now_playing():
    if not all([LASTFM_API_KEY, LASTFM_USERNAME]):
        raise HTTPException(
            status_code=500,
            detail="Sunucu yapılandırılmamış. Lütfen Last.fm değişkenlerini kontrol edin."
        )

    try:
        data = get_lastfm_recent_tracks()
        recent_tracks = data.get("recenttracks", {}).get("track", [])

        if not recent_tracks:
            response_data = NowPlayingResponse(
                track="Bilinmiyor", artist="Bilinmiyor", album_cover=None,
                track_link=None, currently_playing=False
            )
        else:
            latest_track = recent_tracks[0]
            is_playing = latest_track.get("@attr", {}).get("nowplaying") == "true"

            if is_playing:
                response_data = NowPlayingResponse(
                    track=latest_track.get("name"),
                    artist=latest_track.get("artist", {}).get("#text"),
                    album_cover=latest_track.get("image", [{}, {}, {}, {"#text": None}])[3].get("#text"),
                    track_link=latest_track.get("url"),
                    currently_playing=True,
                )
            else:
                response_data = NowPlayingResponse(
                    track="En son dinlenen", artist="Şu anda bir şey çalmıyor", album_cover=None,
                    track_link=None, currently_playing=False
                )

        json_content = response_data.model_dump_json()
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Cache-Control": "s-maxage=15, stale-while-revalidate"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Last.fm verisi alınırken hata: {str(e)}")

handler = Mangum(app)