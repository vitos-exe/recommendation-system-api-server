from datetime import datetime, timedelta
from typing import Any
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.mood_record import MoodRecord
from app.models.user import User
from app.schemas.mood import MoodBase, MoodStatistics

router = APIRouter()


@router.get("/statistics", response_model=MoodStatistics)
def get_mood_statistics(
    days: int = Query(
        7, description="Number of days to include in statistics", ge=1, le=30
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get mood statistics for the current user over a period of time"""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get mood records in the date range
    mood_records = (
        db.query(MoodRecord)
        .filter(
            MoodRecord.user_id == current_user.id,
            MoodRecord.recorded_at >= start_date,
            MoodRecord.recorded_at <= end_date,
        )
        .all()
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "records": mood_records,
    }


@router.get("/current", response_model=MoodBase)
def get_current_mood(
    minutes: int = Query(
        60, description="Number of minutes to consider for current mood", ge=1, le=1440
    ),
    decay_rate: float = Query(
        0.05, description="Decay rate for weighting recent moods more. Higher value means faster decay.", ge=0.001, le=1.0
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the current mood for the user based on recent mood records"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(minutes=minutes)

    # Get mood records in the date range
    mood_records = (
        db.query(MoodRecord)
        .filter(
            MoodRecord.user_id == current_user.id,
            MoodRecord.recorded_at >= start_date,
            MoodRecord.recorded_at <= end_date,
        )
        .order_by(MoodRecord.recorded_at.desc())
        .all()
    )

    weighted_happy_sum = 0.0
    weighted_sad_sum = 0.0
    weighted_angry_sum = 0.0
    weighted_relaxed_sum = 0.0
    total_weight = 0.0

    for record in mood_records:
        age_in_minutes = (end_date - record.recorded_at).total_seconds() / 60.0
        weight = math.exp(-decay_rate * age_in_minutes)

        weighted_happy_sum += record.happy * weight
        weighted_sad_sum += record.sad * weight
        weighted_angry_sum += record.angry * weight
        weighted_relaxed_sum += record.relaxed * weight
        total_weight += weight

    if total_weight == 0:
        raise HTTPException(
            status_code=404,
            detail="No mood records found in the specified time range",
        )

    return {
        "happy": weighted_happy_sum / total_weight,
        "sad": weighted_sad_sum / total_weight,
        "angry": weighted_angry_sum / total_weight,
        "relaxed": weighted_relaxed_sum / total_weight,
    }
