\
from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.mood_record import MoodRecord
from app.models.user import User
from app.schemas.spotify import SpotifyTrack
from app.services.lyrics_client import get_lyrics_for_song_async
from app.services.mood_client import predict_mood_from_lyrics
from app.services.spotify_client import refresh_token


async def ensure_spotify_token_valid(current_user: User, db: Session) -> None:
    if (
        current_user.spotify_token_expiry
        and current_user.spotify_token_expiry < datetime.utcnow()
    ):
        if not current_user.spotify_refresh_token:
            raise HTTPException(
                status_code=400,
                detail="Spotify session expired. Please reconnect your Spotify account.",
            )

        try:
            token_info = await refresh_token(current_user.spotify_refresh_token)
            current_user.spotify_access_token = token_info["access_token"]
            if token_info.get("refresh_token"):
                current_user.spotify_refresh_token = token_info["refresh_token"]
            current_user.spotify_token_expiry = datetime.utcnow() + timedelta(
                seconds=token_info["expires_in"]
            )
            db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Error refreshing Spotify token: {str(e)}"
            )


async def analyze_and_store_mood_for_tracks(
    tracks: List[SpotifyTrack],
    db: Session,
    current_user: User,
):
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
            continue

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
                    spotify_track_id=track.id,
                    spotify_played_at=track.played_at,
                )
                db.add(db_mood_record)
    db.commit()
