from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.mood_record import MoodRecord
from app.models.user import User
from app.schemas.mood import MoodCreate
from app.schemas.mood import MoodRecord as MoodRecordSchema
from app.schemas.mood import MoodStatistics

router = APIRouter()


@router.post("/record", response_model=MoodRecordSchema)
def record_mood(
    mood_in: MoodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Record a new mood entry for the current user"""
    # Create mood record
    db_mood = MoodRecord(
        user_id=current_user.id,
        happy_score=mood_in.happy_score,
        sad_score=mood_in.sad_score,
        angry_score=mood_in.angry_score,
        relaxed_score=mood_in.relaxed_score,
        notes=mood_in.notes,
        recorded_at=datetime.utcnow(),
    )

    db.add(db_mood)
    db.commit()
    db.refresh(db_mood)

    return db_mood


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

    if not mood_records:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "records": [],
            "average_happy": 0.0,
            "average_sad": 0.0,
            "average_angry": 0.0,
            "average_relaxed": 0.0,
        }

    # Calculate averages
    happy_sum = sum(record.happy_score for record in mood_records)
    sad_sum = sum(record.sad_score for record in mood_records)
    angry_sum = sum(record.angry_score for record in mood_records)
    relaxed_sum = sum(record.relaxed_score for record in mood_records)

    record_count = len(mood_records)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "records": mood_records,
        "average_happy": happy_sum / record_count,
        "average_sad": sad_sum / record_count,
        "average_angry": angry_sum / record_count,
        "average_relaxed": relaxed_sum / record_count,
    }


@router.get("/current", response_model=Dict[str, float])
def get_current_mood(
    days: int = Query(
        1, description="Number of days to consider for current mood", ge=1, le=7
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the current mood for the user based on recent mood records"""
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

    if not mood_records:
        return {"happy": 0.25, "sad": 0.25, "angry": 0.25, "relaxed": 0.25}

    # Calculate current mood vector
    happy_sum = sum(record.happy_score for record in mood_records)
    sad_sum = sum(record.sad_score for record in mood_records)
    angry_sum = sum(record.angry_score for record in mood_records)
    relaxed_sum = sum(record.relaxed_score for record in mood_records)

    record_count = len(mood_records)

    return {
        "happy": happy_sum / record_count,
        "sad": sad_sum / record_count,
        "angry": angry_sum / record_count,
        "relaxed": relaxed_sum / record_count,
    }
