from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.config import settings, logger
from app.database import get_db
from app.models.user import User
from app.schemas.recommendation import RecommendedSong
from app.schemas.spotify import SpotifyAuth, SpotifyTrack
from app.services.spotify_client import (
    add_track_to_queue,
    exchange_code_for_token,
    get_auth_url,
    get_recently_played_tracks,
    search_track,
)
from app.services.spotify_service import (
    analyze_and_store_mood_for_tracks,
    ensure_spotify_token_valid,
)

router = APIRouter()

state_user_map: Dict[str, int] = {}


@router.get("/auth", response_model=SpotifyAuth)
async def spotify_auth(current_user: User = Depends(get_current_user)) -> Any:
    logger.info(f"User {current_user.id} starting Spotify authentication flow")
    auth_info = get_auth_url()
    state_user_map[auth_info["state"]] = current_user.id
    logger.debug(f"Generated Spotify auth URL with state {auth_info['state']} for user {current_user.id}")
    return {"auth_url": auth_info["auth_url"], "state": auth_info["state"]}


@router.get("/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    logger.info(f"Received Spotify callback with state: {state}")
    user_id = state_user_map.pop(state, None)

    if user_id is None:
        logger.warning(f"Invalid or expired state parameter in Spotify callback: {state}")
        raise HTTPException(
            status_code=400, detail="Invalid or expired state parameter."
        )

    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        logger.warning(f"User not found for state: {state}")
        raise HTTPException(status_code=404, detail="User not found for state.")

    try:
        logger.debug(f"Exchanging authorization code for Spotify tokens for user {user_id}")
        token_info = await exchange_code_for_token(code)

        current_user.spotify_access_token = token_info["access_token"]
        current_user.spotify_refresh_token = token_info["refresh_token"]
        current_user.spotify_token_expiry = datetime.utcnow() + timedelta(
            seconds=token_info["expires_in"]
        )

        db.commit()
        logger.info(f"Spotify authentication successful for user {user_id}")
    except Exception as e:
        logger.error(f"Error during Spotify token exchange for user {user_id}: {str(e)}")
        raise
    finally:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/home")


@router.get("/recent-tracks", response_model=List[SpotifyTrack])
async def get_recent_tracks(
    background_tasks: BackgroundTasks,
    limit: int = Query(20, ge=1, le=50),
    time_limit_minutes: Optional[int] = Query(30, ge=1),
    analyze_mood: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get user's recently played tracks from Spotify"""
    logger.info(f"Getting {limit} recent tracks for user {current_user.id}, time limit: {time_limit_minutes} minutes, analyze mood: {analyze_mood}")
    if not current_user.spotify_access_token:
        logger.warning(f"User {current_user.id} attempted to get recent tracks without Spotify authentication")
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )

    await ensure_spotify_token_valid(current_user, db)
    logger.debug(f"Spotify token validated for user {current_user.id}")

    tracks = await get_recently_played_tracks(
        access_token=current_user.spotify_access_token,
        limit=limit,
        time_limit_minutes=time_limit_minutes,
    )
    logger.info(f"Retrieved {len(tracks)} recent tracks for user {current_user.id}")
    
    if analyze_mood and tracks:
        logger.debug(f"Scheduling mood analysis for {len(tracks)} tracks from user {current_user.id}")
        background_tasks.add_task(
            analyze_and_store_mood_for_tracks, tracks, db, current_user
        )
    return tracks


@router.post("/queue-song")
async def queue_song_in_spotify(
    song: RecommendedSong,
    current_user: User = Depends(get_current_user),
) -> Any:
    logger.info(f"User {current_user.id} attempting to queue song: '{song.title}' by '{song.artist}'")
    if not current_user.spotify_access_token:
        logger.warning(f"User {current_user.id} attempted to queue a song without Spotify authentication")
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )
    track_uri = await search_track(
        current_user.spotify_access_token, song.title, song.artist
    )
    if not track_uri:
        logger.warning(f"Song '{song.title}' by '{song.artist}' not found on Spotify for user {current_user.id}")
        raise HTTPException(
            status_code=404,
            detail=f"Song '{song.title}' by '{song.artist}' not found on Spotify.",
        )
    logger.debug(f"Found track URI for '{song.title}' by '{song.artist}': {track_uri}")
    await add_track_to_queue(current_user.spotify_access_token, track_uri)
    logger.info(f"Successfully queued song '{song.title}' by '{song.artist}' for user {current_user.id}")
    return {"success": True, "message": f"Added '{song.title}' by '{song.artist}' to your Spotify queue"}
