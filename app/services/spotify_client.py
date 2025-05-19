import uuid
from typing import Dict, List
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.schemas.spotify import SpotifyTrack


def get_auth_url() -> Dict[str, str]:
    """Generate a Spotify authentication URL"""
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


async def exchange_code_for_token(code: str) -> Dict[str, str]:
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
    access_token: str, limit: int = 20, time_range: str = "short_term"
) -> List[SpotifyTrack]:
    """Get user's recently played tracks"""
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.spotify.com/v1/me/player/recently-played?limit={limit}",
            headers=headers,
        )

        if response.status_code != 200:
            raise ValueError(f"Error fetching recently played tracks: {response.text}")

        data = response.json()
        tracks = []

        for item in data.get("items", []):
            track = item.get("track", {})
            artists = [artist["name"] for artist in track.get("artists", [])]

            tracks.append(
                SpotifyTrack(
                    id=track.get("id", ""),
                    name=track.get("name", ""),
                    artist=", ".join(artists),
                    album=track.get("album", {}).get("name", ""),
                    preview_url=track.get("preview_url"),
                )
            )

        return tracks


async def add_track_to_queue(access_token: str, track_uri: str) -> bool:
    """Add a track to the user's queue"""
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}",
            headers=headers,
        )

        return response.status_code == 204
