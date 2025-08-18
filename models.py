from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, unique=True, index=True)
    display_name = Column(String)
    profile_pic_url = Column(String, nullable=True)

    token = relationship("Token", uselist=False, back_populates="user")
    active_share = relationship("ActiveShare", uselist=False, back_populates="user")
    track = relationship("Track", uselist=False, back_populates="user")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="token")


class ActiveShare(Base):
    __tablename__ = "active_shares"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    expires_at = Column(DateTime)

    user = relationship("User", back_populates="active_share")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    track_name = Column(String)
    artist_name = Column(String)
    album_cover_url = Column(String)
    spotify_track_url = Column(String)
    currently_playing = Column(Boolean)

    user = relationship("User", back_populates="track")


# Pydantic Schemas for API
class ShareRequest(BaseModel):
    spotify_id: str

class TrackFeedItem(BaseModel):
    user_id: str
    display_name: str
    spotify_profile_pic: str | None
    current_track: str
    album_cover: str
    spotify_link: str
    currently_playing: bool

    class Config:
        orm_mode = True
