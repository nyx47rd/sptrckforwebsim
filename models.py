from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime
from pydantic import BaseModel

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String)
    profile_pic_url = Column(String, nullable=True)

    token = relationship("Token", back_populates="user", uselist=False)
    track = relationship("Track", back_populates="user", uselist=False)
    active_share = relationship("ActiveShare", back_populates="user", uselist=False)

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="token")

class Track(Base):
    __tablename__ = "tracks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_name = Column(String)
    artist_name = Column(String)
    album_cover_url = Column(String)
    spotify_track_url = Column(String)
    currently_playing = Column(Boolean, default=False)

    user = relationship("User", back_populates="track")

class ActiveShare(Base):
    __tablename__ = "active_shares"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.datetime.utcnow() + datetime.timedelta(hours=24))

    user = relationship("User", back_populates="active_share")

# Pydantic models for request/response validation
class ShareRequest(BaseModel):
    spotify_id: str

