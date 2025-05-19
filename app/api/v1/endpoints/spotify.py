from datetime import datetime, timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.spotify import SpotifyAuth, SpotifyTrack
from app.services.spotify_client import (
    exchange_code_for_token,
    get_auth_url,
    get_recently_played_tracks,
    refresh_token,
)

router = APIRouter()


@router.get("/auth", response_model=SpotifyAuth)
async def spotify_auth() -> Any:
    """Get Spotify authorization URL"""
    return get_auth_url()


@router.get("/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Spotify OAuth callback handler"""
    try:
        token_info = await exchange_code_for_token(code)

        # Store tokens in user's record
        current_user.spotify_access_token = token_info["access_token"]
        current_user.spotify_refresh_token = token_info["refresh_token"]
        current_user.spotify_token_expiry = datetime.utcnow() + timedelta(
            seconds=token_info["expires_in"]
        )

        db.commit()

        return {"message": "Authentication successful"}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error authenticating with Spotify: {str(e)}"
        )


@router.get("/recent-tracks", response_model=List[SpotifyTrack])
async def get_recent_tracks(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get user's recently played tracks from Spotify"""
    if not current_user.spotify_access_token:
        raise HTTPException(
            status_code=400,
            detail="Not authenticated with Spotify. Please connect your Spotify account first.",
        )

    # Check if token is expired and refresh if needed
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

    try:
        tracks = await get_recently_played_tracks(
            access_token=current_user.spotify_access_token, limit=limit
        )
        return tracks
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error fetching recently played tracks: {str(e)}"
        )
