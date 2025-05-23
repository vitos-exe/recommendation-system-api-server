from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.config import settings
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
    auth_info = get_auth_url()
    state_user_map[auth_info["state"]] = current_user.id
    return {"auth_url": auth_info["auth_url"], "state": auth_info["state"]}


@router.get("/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    user_id = state_user_map.pop(state, None)

    if user_id is None:
        raise HTTPException(
            status_code=400, detail="Invalid or expired state parameter."
        )

    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found for state.")

    try:
        token_info = await exchange_code_for_token(code)

        current_user.spotify_access_token = token_info["access_token"]
        current_user.spotify_refresh_token = token_info["refresh_token"]
        current_user.spotify_token_expiry = datetime.utcnow() + timedelta(
            seconds=token_info["expires_in"]
        )

        db.commit()
    finally:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/main/home")


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
    if not current_user.spotify_access_token:
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )

    await ensure_spotify_token_valid(current_user, db)

    tracks = await get_recently_played_tracks(
        access_token=current_user.spotify_access_token,
        limit=limit,
        time_limit_minutes=time_limit_minutes,
    )
    if analyze_mood and tracks:
        background_tasks.add_task(
            analyze_and_store_mood_for_tracks, tracks, db, current_user
        )
    return tracks


@router.post("/queue-song")
async def queue_song_in_spotify(
    song: RecommendedSong,
    current_user: User = Depends(get_current_user),
) -> Any:
    if not current_user.spotify_access_token:
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )
    track_uri = await search_track(
        current_user.spotify_access_token, song.title, song.artist
    )
    if not track_uri:
        raise HTTPException(
            status_code=404,
            detail=f"Song '{song.title}' by '{song.artist}' not found on Spotify.",
        )
    await add_track_to_queue(current_user.spotify_access_token, track_uri)
