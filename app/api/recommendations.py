from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.mood import get_current_mood
from app.config import logger
from app.database import get_db
from app.models.user import User
from app.schemas.mood import MoodBase
from app.schemas.recommendation import RecommendedSong
from app.services.mood_client import get_recommendations_for_mood

router = APIRouter()


@router.get("", response_model=List[RecommendedSong])
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
    logger.info(f"Getting recommendations for user {current_user.id} with limit {limit}. Use current mood: {use_current_mood}.")
    if use_current_mood:
        logger.debug(f"Using current mood for user {current_user.id}.")
        current_mood_dict = get_current_mood(
            minutes=30, decay_rate=0.05, db=db, current_user=current_user
        )
        target_mood = MoodBase(**current_mood_dict)
    else:
        logger.debug(f"Using provided mood for user {current_user.id}: happy={happy}, sad={sad}, angry={angry}, relaxed={relaxed}.")
        if happy is None or sad is None or angry is None or relaxed is None:
            logger.warning(f"Missing mood parameters for user {current_user.id} when not using current mood.")
            raise HTTPException(
                status_code=400,
                detail="When not using current mood, all mood parameters (happy, sad, angry, relaxed) must be provided",
            )
        target_mood = MoodBase(happy=happy, sad=sad, angry=angry, relaxed=relaxed)
    logger.info(f"Target mood for recommendations for user {current_user.id}: {target_mood}")
    recommendations = await get_recommendations_for_mood(target_mood, limit)
    logger.info(f"Returning {len(recommendations)} recommendations for user {current_user.id}.")
    return recommendations
