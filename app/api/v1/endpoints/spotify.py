from datetime import datetime, timedelta
from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
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
from app.config import settings

router = APIRouter()

# WARNING: This is a simple in-memory store for demonstration.
# In a production environment, especially with multiple server instances,
# use a shared store like Redis or a database table for this.
state_user_map: Dict[str, int] = {}


@router.get("/auth", response_model=SpotifyAuth)
async def spotify_auth(current_user: User = Depends(get_current_user)) -> Any:
    """Get Spotify authorization URL"""
    auth_info = get_auth_url()
    # Store the user_id associated with this state for the callback
    state_user_map[auth_info["state"]] = current_user.id
    return {"auth_url": auth_info["auth_url"], "state": auth_info["state"]}


@router.get("/callback")
async def spotify_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> Any:
    """Spotify OAuth callback handler"""
    # Retrieve user_id using state
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

        # Store tokens in user's record
        current_user.spotify_access_token = token_info["access_token"]
        current_user.spotify_refresh_token = token_info["refresh_token"]
        current_user.spotify_token_expiry = datetime.utcnow() + timedelta(
            seconds=token_info["expires_in"]
        )

        db.commit()

        # Redirect to frontend home page
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/home?spotify_auth=success")
    except Exception as e:
        # Redirect to frontend with error query param
        error_message = f"Error authenticating with Spotify: {str(e)}"
        import urllib.parse
        encoded_error = urllib.parse.quote(error_message)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/home?spotify_auth=error&error_detail={encoded_error}")


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
