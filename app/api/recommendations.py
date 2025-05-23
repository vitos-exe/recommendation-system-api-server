from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.mood import get_current_mood
from app.database import get_db
from app.models.user import User
from app.schemas.mood import MoodBase
from app.schemas.recommendation import RecommendedSong
from app.services.mood_client import get_recommendations_for_mood

router = APIRouter()


@router.get("/get-recommendations", response_model=List[RecommendedSong])
async def get_music_recommendations(
    limit: int = Query(5, ge=1, le=10),
    use_current_mood: bool = Query(True),
    happy: float = Query(None, ge=0.0, le=1.0),
    sad: float = Query(None, ge=0.0, le=1.0),
    angry: float = Query(None, ge=0.0, le=1.0),
    relaxed: float = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    target_mood: MoodBase
    if use_current_mood:
        current_mood_dict = get_current_mood(
            minutes=30, db=db, current_user=current_user
        )
        target_mood = MoodBase(**current_mood_dict)
    else:
        if happy is None or sad is None or angry is None or relaxed is None:
            raise HTTPException(
                status_code=400,
                detail="When not using current mood, all mood parameters (happy, sad, angry, relaxed) must be provided",
            )
        target_mood = MoodBase(happy=happy, sad=sad, angry=angry, relaxed=relaxed)
    return await get_recommendations_for_mood(target_mood, limit)
