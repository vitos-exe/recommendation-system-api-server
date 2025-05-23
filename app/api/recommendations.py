from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.mood import get_current_mood
from app.database import get_db
from app.models.mood_record import MoodRecord
from app.models.user import User
from app.schemas.mood import MoodBase
from app.schemas.recommendation import RecommendedSong
from app.services.lyrics_client import get_lyrics_for_song_async
from app.services.mood_client import (
    get_recommendations_for_mood,
    predict_mood_from_lyrics,
)
from app.services.spotify_client import (
    get_recently_played_tracks,
)

router = APIRouter()


@router.get("/analyze-recent-tracks", status_code=status.HTTP_204_NO_CONTENT)
async def analyze_recent_tracks(
    limit: int = Query(10, ge=1, le=50),
    time_limit_minutes: int = Query(30, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Analyze user's recently played tracks to determine mood profile and store individual moods."""
    if not current_user.spotify_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )

    tracks = await get_recently_played_tracks(
        access_token=current_user.spotify_access_token,
        limit=limit,
        time_limit_minutes=time_limit_minutes,
    )

    if not tracks:
        return

    for track in tracks:
        existing_record = (
            db.query(MoodRecord)
            .filter_by(
                user_id=current_user.id,
                spotify_track_id=track.id,
                spotify_played_at=track.played_at,
            )
            .first()
        )
        if existing_record:
            continue  # Skip if already processed

        lyrics = await get_lyrics_for_song_async(track.name, track.artist)

        if lyrics:
            mood_prediction = await predict_mood_from_lyrics(
                lyrics, track.artist, track.name
            )
            if mood_prediction:
                db_mood_record = MoodRecord(
                    user_id=current_user.id,
                    happy=mood_prediction.happy,
                    sad=mood_prediction.sad,
                    angry=mood_prediction.angry,
                    relaxed=mood_prediction.relaxed,
                    notes=f"Mood generated from track: {track.name} by {track.artist}",
                    recorded_at=datetime.utcnow(),
                    spotify_track_id=track.id,  # Store Spotify track ID
                    spotify_played_at=track.played_at,  # Store Spotify played_at timestamp
                )
                db.add(db_mood_record)

    db.commit()


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
        current_mood_dict = get_current_mood(days=1, db=db, current_user=current_user)
        target_mood = MoodBase(**current_mood_dict)
    else:
        if happy is None or sad is None or angry is None or relaxed is None:
            raise HTTPException(
                status_code=400,
                detail="When not using current mood, all mood parameters (happy, sad, angry, relaxed) must be provided",
            )
        target_mood = MoodBase(happy=happy, sad=sad, angry=angry, relaxed=relaxed)
    return await get_recommendations_for_mood(target_mood, limit)
