import datetime
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.schemas.spotify import SpotifyTrack


def get_auth_url() -> Dict[str, str]:
    """Generate a Spotify authentication URL and state"""
    # Generate a random state to prevent CSRF
    state = str(uuid.uuid4())

    # Parameters for the auth URL
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "state": state,
        "scope": "user-read-recently-played user-modify-playback-state",
    }

    # Construct the auth URL
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"

    return {"auth_url": auth_url, "state": state}


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
                "client_id": settings.SPOTIFY_CLIENT_ID,
                "client_secret": settings.SPOTIFY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise ValueError(f"Error getting token: {response.text}")

        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_in": data["expires_in"],
            "token_type": data["token_type"],
        }


async def refresh_token(refresh_token: str) -> Dict[str, str]:
    """Refresh an expired access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.SPOTIFY_CLIENT_ID,
                "client_secret": settings.SPOTIFY_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise ValueError(f"Error refreshing token: {response.text}")

        data = response.json()
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", refresh_token),
            "expires_in": data["expires_in"],
            "token_type": data["token_type"],
        }


async def get_recently_played_tracks(
    access_token: str, limit: int = 20, time_limit_minutes: Optional[int] = None
) -> List[SpotifyTrack]:
    """Get user's recently played tracks"""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": limit}

    if time_limit_minutes:
        after_timestamp = int(
            (
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.timedelta(minutes=time_limit_minutes)
            ).timestamp()
            * 1000
        )
        params["after"] = after_timestamp

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.spotify.com/v1/me/player/recently-played",
            headers=headers,
            params=params,
        )

        if response.status_code != 200:
            raise ValueError(f"Error fetching recently played tracks: {response.text}")

        data = response.json()
        tracks = []

        for item in data.get("items", []):
            track = item.get("track", {})
            artists = [artist["name"] for artist in track.get("artists", [])]
            played_at_str = item.get("played_at")
            played_at = None
            if played_at_str:
                played_at = datetime.datetime.fromisoformat(
                    played_at_str.replace("Z", "+00:00")
                )

            tracks.append(
                SpotifyTrack(
                    id=track.get("id", ""),
                    name=track.get("name", ""),
                    artist=", ".join(artists),
                    album=track.get("album", {}).get("name", ""),
                    uri=track.get("uri", ""),
                    played_at=played_at,
                    preview_url=track.get("preview_url"),
                )
            )

        return tracks


async def add_track_to_queue(access_token: str, track_uri: str) -> None:
    """Add a track to the user's queue"""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}",
            headers=headers,
        )
        response.raise_for_status()


async def search_track(
    access_token: str, track_name: str, artist_name: str
) -> Optional[str]:
    """Search for a track on Spotify by name and artist and return its URI."""
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": f"track:{track_name} artist:{artist_name}",
        "type": "track",
        "limit": 1,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.spotify.com/v1/search", headers=headers, params=params
        )
        response.raise_for_status()

        data = response.json()
        tracks = data.get("tracks", {}).get("items", [])
        if not tracks:
            return None

        return tracks[0].get("uri")
