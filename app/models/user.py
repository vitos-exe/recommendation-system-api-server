from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean(), default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Spotify credentials
    spotify_access_token = Column(Text, nullable=True)
    spotify_refresh_token = Column(Text, nullable=True)
    spotify_token_expiry = Column(DateTime, nullable=True)

    # Relationships
    mood_records = relationship("MoodRecord", back_populates="user")
