from sqlalchemy import String, ForeignKey, Integer, Text, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from .base import BaseModel
from .auth import User
import uuid6
from app.extensions import db

class PetProfile(BaseModel):
    __tablename__ = 'pet_profiles'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(50)) # dog, cat, other
    breed: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[str]] = mapped_column(String(20)) # male, female, unknown
    birth_date: Mapped[Optional[str]] = mapped_column(String(50))
    adoption_date: Mapped[Optional[str]] = mapped_column(String(50)) # celebration day
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1024))
    description: Mapped[Optional[str]] = mapped_column(Text)
    # media: Mapped[List["Media"]] = relationship(secondary="media_pets", back_populates="pets") # Defined later or use string

# Association Table for Media <-> Pet
media_pets = Table(
    'media_pets',
    db.metadata,
    Column('media_id', db.Uuid, ForeignKey('media.id'), primary_key=True),
    Column('pet_id', db.Uuid, ForeignKey('pet_profiles.id'), primary_key=True)
)

# Association Table for Media <-> Tag
media_tags = Table(
    'media_tags',
    db.metadata,
    Column('media_id', db.Uuid, ForeignKey('media.id'), primary_key=True),
    Column('tag_id', db.Uuid, ForeignKey('tags.id'), primary_key=True)
)

# Association Table for Media <-> User (Favorites)
media_favorites = Table(
    'media_favorites',
    db.metadata,
    Column('media_id', db.Uuid, ForeignKey('media.id'), primary_key=True),
    Column('user_id', db.Uuid, ForeignKey('users.id'), primary_key=True),
    Column('created_at', db.DateTime, default=db.func.now())
)

class Tag(BaseModel):
    __tablename__ = 'tags'
    
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # media relationship via secondary

class Media(BaseModel):
    __tablename__ = 'media'
    
    uploader_id: Mapped[uuid6.UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    duration_sec: Mapped[Optional[float]] = mapped_column(Integer) # Float? Integer in design?
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    taken_at: Mapped[Optional[str]] = mapped_column(String(50)) # ISO string
    
    status: Mapped[str] = mapped_column(String(50), default='processing', index=True) # processing, ready, error
    
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1024))
    

    
    uploader: Mapped["User"] = relationship("User") # Add relationship to User
    tags: Mapped[List["Tag"]] = relationship(secondary=media_tags, backref="media")
    pets: Mapped[List["PetProfile"]] = relationship(secondary=media_pets, backref="media")
    # Favorites relationship
    favorited_by: Mapped[List["User"]] = relationship(secondary=media_favorites, backref="favorite_media")
    
    # Albums association can also be here or in Album

class Album(BaseModel):
    __tablename__ = 'albums'
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Many-to-Many with Media (Simplified for now, can use association object if ordering is needed)
    media: Mapped[List["Media"]] = relationship(secondary="album_media")

album_media = Table(
    'album_media',
    db.metadata,
    Column('album_id', db.Uuid, ForeignKey('albums.id'), primary_key=True),
    Column('media_id', db.Uuid, ForeignKey('media.id'), primary_key=True),
    Column('created_at', db.DateTime, default=db.func.now())
)
