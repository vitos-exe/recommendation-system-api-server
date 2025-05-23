from datetime import datetime, timedelta
from typing import Any

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the current mood for the user based on recent mood records"""
    # Calculate date range
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
        .all()
    )

    if not mood_records:
        raise HTTPException(
            status_code=404, detail="No mood records found for this period."
        )

    # Calculate current mood vector
    happy_sum = sum(record.happy for record in mood_records)
    sad_sum = sum(record.sad for record in mood_records)
    angry_sum = sum(record.angry for record in mood_records)
    relaxed_sum = sum(record.relaxed for record in mood_records)

    record_count = len(mood_records)

    return {
        "happy": happy_sum / record_count,
        "sad": sad_sum / record_count,
        "angry": angry_sum / record_count,
        "relaxed": relaxed_sum / record_count,
    }
