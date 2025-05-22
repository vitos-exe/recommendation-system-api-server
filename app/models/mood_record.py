from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class MoodRecord(Base):
    __tablename__ = "mood_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    recorded_at = Column(DateTime, default=datetime.utcnow)

    # Emotional profile vectors
    happy = Column(Float, default=0.0)
    sad = Column(Float, default=0.0)
    angry = Column(Float, default=0.0)
    relaxed = Column(Float, default=0.0)

    # Optional notes about the mood record
    notes = Column(String(255), nullable=True)

    # Spotify track information to prevent duplicates
    spotify_track_id = Column(String, nullable=True, index=True)
    spotify_played_at = Column(DateTime, nullable=True, index=True)

    # Relationship
    user = relationship("User", back_populates="mood_records")
