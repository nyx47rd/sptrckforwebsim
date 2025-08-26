import os
import datetime
import base64
from urllib.parse import urlencode
import requests

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import RedirectResponse
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# --- .ENV LOADING ---
load_dotenv()

# --- SPOTIFY SETUP ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
SCOPES = "user-read-currently-playing user-read-playback-state"

def spotify_get_auth_url():
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"

def spotify_get_token_data_from_code(code: str):
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("ascii")).decode("ascii")
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {auth_header}"},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": SPOTIFY_REDIRECT_URI},
    )
    response.raise_for_status()
    token_data = response.json()
    token_data["expires_at"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=token_data["expires_in"])
    return token_data

def spotify_refresh_access_token(refresh_token: str):
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("ascii")).decode("ascii")
    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {auth_header}"},
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
    )
    response.raise_for_status()
    token_data = response.json()
    token_data["expires_at"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=token_data["expires_in"])
    return token_data

def spotify_get_user_profile(access_token: str):
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/me", headers={"Authorization": f"Bearer {access_token}"})
    response.raise_for_status()
    return response.json()

def spotify_get_currently_playing(access_token: str):
    response = requests.get(f"{SPOTIFY_API_BASE_URL}/me/player/currently-playing", headers={"Authorization": f"Bearer {access_token}"})
    if response.status_code == 204:
        return None
    response.raise_for_status()
    return response.json()

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- MODELS ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, unique=True, index=True)
    display_name = Column(String)
    profile_pic_url = Column(String, nullable=True)
    token = relationship("Token", uselist=False, back_populates="user")

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(DateTime)
    user = relationship("User", back_populates="token")

# --- PYDANTIC SCHEMAS ---
class TrackFeedItem(BaseModel):
    user_id: str
    display_name: str
    spotify_profile_pic: str | None
    current_track: str
    album_cover: str
    spotify_link: str
    currently_playing: bool

# --- CRUD OPERATIONS ---
def crud_get_user_by_spotify_id(db: Session, spotify_id: str):
    return db.query(User).filter(User.spotify_id == spotify_id).first()

def crud_create_user(db: Session, spotify_id: str, display_name: str, profile_pic_url: str | None):
    db_user = User(spotify_id=spotify_id, display_name=display_name, profile_pic_url=profile_pic_url)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def crud_create_or_update_token(db: Session, user_id: int, access_token: str, refresh_token: str, expires_at: datetime.datetime):
    db_token = db.query(Token).filter(Token.user_id == user_id).first()
    if db_token:
        db_token.access_token = access_token
        db_token.refresh_token = refresh_token
        db_token.expires_at = expires_at
    else:
        db_token = Token(user_id=user_id, access_token=access_token, refresh_token=refresh_token, expires_at=expires_at)
        db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

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
    return {"message": "Now Listening API"}

@app.get("/api/auth/login")
def auth_login():
    return RedirectResponse(spotify_get_auth_url())

@app.get("/api/auth/callback")
def auth_callback(code: str, db: Session = Depends(get_db)):
    try:
        token_data = spotify_get_token_data_from_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Could not retrieve token from Spotify.") from e
    user_profile = spotify_get_user_profile(token_data["access_token"])
    user = crud_get_user_by_spotify_id(db, spotify_id=user_profile["id"])
    if not user:
        user = crud_create_user(
            db=db, spotify_id=user_profile["id"], display_name=user_profile["display_name"],
            profile_pic_url=user_profile["images"][0]["url"] if user_profile.get("images") else None
        )
    crud_create_or_update_token(
        db=db, user_id=user.id, access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"], expires_at=token_data["expires_at"]
    )

    frontend_url = "https://websim.com/@ysr/profile/"
    params = {
        "spotify_id": user.spotify_id,
        "display_name": user.display_name
    }
    return RedirectResponse(f"{frontend_url}?{urlencode(params)}")

@app.get("/api/now-playing/{spotify_id}", response_model=TrackFeedItem)
def now_playing(spotify_id: str, db: Session = Depends(get_db)):
    user = crud_get_user_by_spotify_id(db, spotify_id=spotify_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    token = user.token
    if not token:
        raise HTTPException(status_code=404, detail="Token not found for user.")

    # Refresh token if it's expired
    if token.expires_at < datetime.datetime.utcnow():
        try:
            new_token_data = spotify_refresh_access_token(token.refresh_token)
            token = crud_create_or_update_token(
                db, user.id, new_token_data["access_token"],
                token.refresh_token, new_token_data["expires_at"]
            )
        except Exception:
            # If refresh fails, we can't get data.
            raise HTTPException(status_code=503, detail="Could not refresh Spotify token.")

    # Fetch currently playing track
    currently_playing = spotify_get_currently_playing(token.access_token)
    if currently_playing and currently_playing.get("is_playing"):
        item = currently_playing.get("item", {})
        if not item:
            # This can happen for podcasts etc.
            return TrackFeedItem(
                user_id=user.spotify_id, display_name=user.display_name,
                spotify_profile_pic=user.profile_pic_url, current_track="Playing something not exposed by API",
                album_cover="", spotify_link="", currently_playing=True
            )

        track_name = item.get("name")
        artist_name = ", ".join(artist.get("name") for artist in item.get("artists", []))
        album_cover_url = item.get("album", {}).get("images", [{}])[0].get("url")
        spotify_track_url = item.get("external_urls", {}).get("spotify")

        return TrackFeedItem(
            user_id=user.spotify_id,
            display_name=user.display_name,
            spotify_profile_pic=user.profile_pic_url,
            current_track=f"{track_name} by {artist_name}",
            album_cover=album_cover_url,
            spotify_link=spotify_track_url,
            currently_playing=True,
        )
    else:
        return TrackFeedItem(
            user_id=user.spotify_id,
            display_name=user.display_name,
            spotify_profile_pic=user.profile_pic_url,
            current_track="Not currently listening",
            album_cover="",
            spotify_link="",
            currently_playing=False,
        )
