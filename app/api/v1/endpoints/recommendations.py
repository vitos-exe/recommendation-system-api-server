from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.services.mood_client import get_recommendations_for_mood, predict_mood_from_lyrics
from app.services.lyrics_client import get_lyrics_for_song_async
from app.services.spotify_client import add_track_to_queue, get_recently_played_tracks

router = APIRouter()


@router.get("/analyze-recent-tracks", response_model=Dict[str, Any])
async def analyze_recent_tracks(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Analyze user's recently played tracks to determine mood profile"""
    if not current_user.spotify_access_token:
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )

    try:
        # Get recently played tracks
        tracks = await get_recently_played_tracks(
            access_token=current_user.spotify_access_token, limit=limit
        )

        # Process each track to get lyrics and predict mood
        mood_results = []

        for track in tracks:
            # Get lyrics for the track
            lyrics = await get_lyrics_for_song_async(track.name, track.artist)

            if lyrics:
                # Predict mood from lyrics
                mood = await predict_mood_from_lyrics(lyrics, track.artist, track.name)
                mood_results.append({"track": track, "mood": mood})

        # Calculate average mood vector
        if not mood_results:
            return {"message": "No mood data could be generated from recent tracks"}

        avg_happy = sum(r["mood"]["happy"] for r in mood_results) / len(mood_results)
        avg_sad = sum(r["mood"]["sad"] for r in mood_results) / len(mood_results)
        avg_angry = sum(r["mood"]["angry"] for r in mood_results) / len(mood_results)
        avg_relaxed = sum(r["mood"]["relaxed"] for r in mood_results) / len(
            mood_results
        )

        avg_mood = {
            "happy": avg_happy,
            "sad": avg_sad,
            "angry": avg_angry,
            "relaxed": avg_relaxed,
        }

        # Store the mood data in the database
        from datetime import datetime

        from app.models.mood_record import MoodRecord

        db_mood = MoodRecord(
            user_id=current_user.id,
            happy_score=avg_happy,
            sad_score=avg_sad,
            angry_score=avg_angry,
            relaxed_score=avg_relaxed,
            notes="Generated from recent listening history",
            recorded_at=datetime.utcnow(),
        )

        db.add(db_mood)
        db.commit()

        return {
            "tracks_analyzed": len(mood_results),
            "average_mood": avg_mood,
            "detailed_results": mood_results,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error analyzing recent tracks: {str(e)}"
        )


@router.get("/get-recommendations", response_model=List[Dict[str, Any]])
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
    """Get music recommendations based on mood"""
    try:
        # Determine which mood vector to use
        if use_current_mood:
            # Use the user's current mood from records
            from app.api.v1.endpoints.mood import get_current_mood

            mood_vector = get_current_mood(days=1, db=db, current_user=current_user)
        else:
            # Use the provided custom mood
            if happy is None or sad is None or angry is None or relaxed is None:
                raise HTTPException(
                    status_code=400,
                    detail="When not using current mood, all mood parameters (happy, sad, angry, relaxed) must be provided",
                )

            mood_vector = {
                "happy": happy,
                "sad": sad,
                "angry": angry,
                "relaxed": relaxed,
            }

        # Get song recommendations from AI service
        recommendations = await get_recommendations_for_mood(mood_vector, limit)

        if not recommendations:
            raise HTTPException(
                status_code=404, detail="No recommendations found for the given mood"
            )

        return recommendations

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error getting recommendations: {str(e)}"
        )


@router.post("/queue-song")
async def queue_song_in_spotify(
    track_id: str,
    current_user: User = Depends(get_current_user),
) -> Any:
    """Queue a recommended song in the user's Spotify player"""
    if not current_user.spotify_access_token:
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )

    try:
        track_uri = f"spotify:track:{track_id}"
        success = await add_track_to_queue(current_user.spotify_access_token, track_uri)

        if success:
            return {"message": "Track added to queue successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add track to queue")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error adding track to queue: {str(e)}"
        )
