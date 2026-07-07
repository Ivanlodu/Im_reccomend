from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, nullable=False, unique=True)
    display_name = Column(String)
    email = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, nullable=False, unique=True)
    name = Column(String)
    artist = Column(String)
    album = Column(String)
    release_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Artist(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String, nullable=False, unique=True)
    name = Column(String)
    artist_id = Column(Integer, ForeignKey('artists.id'))  # Self-referential foreign key for related artists
    genres = Column(String)  # You might want to store this as a JSON or a separate table for many-to-many relationships
    popularity = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ListenEvent(Base):
    __tablename__ = "listen_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,ForeignKey('users.id'), nullable=False)
    track_id = Column(Integer, ForeignKey('tracks.id'), nullable=False)
    listened_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)