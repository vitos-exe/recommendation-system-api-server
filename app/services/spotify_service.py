from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import logger  # New import
from app.models.mood_record import MoodRecord
from app.models.user import User
from app.schemas.spotify import SpotifyTrack
from app.services.lyrics_client import get_lyrics_for_song_async
from app.services.mood_client import predict_mood_from_lyrics
from app.services.spotify_client import refresh_token


async def ensure_spotify_token_valid(current_user: User, db: Session) -> None:
    logger.debug(f"Checking Spotify token validity for user {current_user.id}")
    
    if (
        current_user.spotify_token_expiry
        and current_user.spotify_token_expiry < datetime.utcnow()
    ):
        logger.info(f"Spotify token expired for user {current_user.id}, attempting to refresh")
        
        if not current_user.spotify_refresh_token:
            logger.warning(f"No refresh token available for user {current_user.id}")
            raise HTTPException(
                status_code=400,
                detail="Spotify session expired. Please reconnect your Spotify account.",
            )

        try:
            logger.debug(f"Refreshing token for user {current_user.id}")
            token_info = await refresh_token(current_user.spotify_refresh_token)
            
            current_user.spotify_access_token = token_info["access_token"]
            if token_info.get("refresh_token"):
                current_user.spotify_refresh_token = token_info["refresh_token"]
                logger.debug(f"Updated refresh token for user {current_user.id}")
                
            current_user.spotify_token_expiry = datetime.utcnow() + timedelta(
                seconds=token_info["expires_in"]
            )
            
            db.commit()
            logger.info(f"Successfully refreshed Spotify token for user {current_user.id}, expires at {current_user.spotify_token_expiry}")
            
        except Exception as e:
            logger.error(f"Failed to refresh Spotify token for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Error refreshing Spotify token: {str(e)}"
            )
    else:
        logger.debug(f"Spotify token for user {current_user.id} is still valid, expires at {current_user.spotify_token_expiry}")


async def analyze_and_store_mood_for_tracks(
    tracks: List[SpotifyTrack],
    db: Session,
    current_user: User,
):
    logger.info(f"Analyzing mood for {len(tracks)} tracks for user {current_user.id}")
    
    if not tracks:
        logger.warning("No tracks provided for mood analysis")
        return

    success_count = 0
    skip_count = 0
    error_count = 0
    
    for track in tracks:
        try:
            # Check if we've already analyzed this track play
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
                logger.debug(f"Skipping mood analysis for track {track.id} ({track.name} by {track.artist}) - already analyzed")
                skip_count += 1
                continue

            logger.debug(f"Processing track: {track.name} by {track.artist}")
            
            # Get lyrics
            lyrics = await get_lyrics_for_song_async(track.name, track.artist)

            if lyrics:
                logger.debug(f"Lyrics found for track: {track.name} by {track.artist}, predicting mood")
                mood_prediction = await predict_mood_from_lyrics(
                    lyrics, track.artist, track.name
                )
                
                if mood_prediction:
                    logger.debug(f"Creating mood record for track {track.id} ({track.name} by {track.artist})")
                    db_mood_record = MoodRecord(
                        user_id=current_user.id,
                        happy=mood_prediction.happy,
                        sad=mood_prediction.sad,
                        angry=mood_prediction.angry,
                        relaxed=mood_prediction.relaxed,
                        notes=f"Mood generated from track: {track.name} by {track.artist}",
                        recorded_at=datetime.utcnow(),
                        spotify_track_id=track.id,
                        spotify_played_at=track.played_at,
                    )
                    db.add(db_mood_record)
                    success_count += 1
                else:
                    logger.warning(f"No mood prediction returned for track: {track.name} by {track.artist}")
                    error_count += 1
            else:
                logger.warning(f"No lyrics found for track: {track.name} by {track.artist}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error analyzing mood for track {track.name} by {track.artist}: {str(e)}")
            error_count += 1
            # Continue with the next track
    
    try:
        db.commit()
        logger.info(f"Mood analysis complete. Success: {success_count}, Skipped: {skip_count}, Errors: {error_count}")
    except Exception as e:
        logger.error(f"Error committing mood records to database: {str(e)}")
        db.rollback()
