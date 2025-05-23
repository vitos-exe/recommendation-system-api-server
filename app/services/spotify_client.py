import datetime
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.config import settings, logger
from app.schemas.spotify import SpotifyTrack


def get_auth_url() -> Dict[str, str]:
    """Generate a Spotify authentication URL and state"""
    logger.info("Generating Spotify authentication URL")
    
    # Generate a random state to prevent CSRF
    state = str(uuid.uuid4())
    logger.debug(f"Generated state for Spotify authentication: {state}")

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
    logger.debug(f"Spotify auth URL generated with redirect to: {settings.SPOTIFY_REDIRECT_URI}")

    return {"auth_url": auth_url, "state": state}


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token"""
    logger.info("Exchanging authorization code for Spotify access token")
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug("Sending token exchange request to Spotify")
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
                error_msg = f"Error getting token: Status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            data = response.json()
            logger.info("Successfully exchanged code for Spotify access token")
            logger.debug(f"Token expires in {data['expires_in']} seconds")
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", ""),
                "expires_in": data["expires_in"],
                "token_type": data["token_type"],
            }
    except Exception as e:
        logger.error(f"Exception during token exchange: {str(e)}")
        raise


async def refresh_token(refresh_token: str) -> Dict[str, str]:
    """Refresh an expired access token"""
    logger.info("Refreshing expired Spotify access token")
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug("Sending token refresh request to Spotify")
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
                error_msg = f"Error refreshing token: Status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            data = response.json()
            logger.info("Successfully refreshed Spotify access token")
            logger.debug(f"New token expires in {data['expires_in']} seconds")
            
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_in": data["expires_in"],
                "token_type": data["token_type"],
            }
    except Exception as e:
        logger.error(f"Exception during token refresh: {str(e)}")
        raise


async def get_recently_played_tracks(
    access_token: str, limit: int = 20, time_limit_minutes: Optional[int] = None
) -> List[SpotifyTrack]:
    """Get user's recently played tracks"""
    logger.info(f"Fetching {limit} recently played Spotify tracks" + 
               (f" from the last {time_limit_minutes} minutes" if time_limit_minutes else ""))
    
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
        logger.debug(f"Using 'after' timestamp: {after_timestamp} ({datetime.datetime.fromtimestamp(after_timestamp/1000)})")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/me/player/recently-played",
                headers=headers,
                params=params,
            )

            if response.status_code != 200:
                error_msg = f"Error fetching recently played tracks: Status {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            data = response.json()
            items = data.get("items", [])
            logger.debug(f"Received {len(items)} items from Spotify API")
            
            tracks = []
            for item in items:
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

            logger.info(f"Successfully retrieved {len(tracks)} recently played tracks")
            return tracks
    except Exception as e:
        logger.error(f"Exception getting recently played tracks: {str(e)}")
        raise


async def add_track_to_queue(access_token: str, track_uri: str) -> None:
    """Add a track to the user's queue"""
    logger.info(f"Adding track to queue: {track_uri}")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.spotify.com/v1/me/player/queue?uri={track_uri}",
                headers=headers,
            )
            response.raise_for_status()
            logger.info(f"Successfully added track {track_uri} to queue")
    except Exception as e:
        logger.error(f"Error adding track to queue: {str(e)}")
        raise


async def search_track(
    access_token: str, track_name: str, artist_name: str
) -> Optional[str]:
    """Search for a track on Spotify by name and artist and return its URI."""
    logger.info(f"Searching for track: '{track_name}' by '{artist_name}'")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "q": f"track:{track_name} artist:{artist_name}",
        "type": "track",
        "limit": 1,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending search request to Spotify API with query: {params['q']}")
            response = await client.get(
                "https://api.spotify.com/v1/search", headers=headers, params=params
            )
            response.raise_for_status()

            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])
            
            if not tracks:
                logger.warning(f"No tracks found for '{track_name}' by '{artist_name}'")
                return None

            track_uri = tracks[0].get("uri")
            logger.info(f"Found track URI for '{track_name}' by '{artist_name}': {track_uri}")
            return track_uri
    except Exception as e:
        logger.error(f"Error searching for track '{track_name}' by '{artist_name}': {str(e)}")
        raise
