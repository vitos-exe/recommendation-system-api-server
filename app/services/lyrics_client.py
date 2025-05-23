from typing import Optional

import httpx
import lyricsgenius

from app.config import settings

OVH_LYRICS_API_URL = "https://api.lyrics.ovh/v1"


async def get_lyrics_from_ovh_async(song_title: str, artist_name: str) -> Optional[str]:
    """
    Async version of the OVH lyrics fetching function for use with FastAPI
    """
    url = f"{OVH_LYRICS_API_URL}/{artist_name}/{song_title}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            return data.get("lyrics")
    finally:
        return None


async def get_lyrics_from_genius_async(
    song_title: str, artist_name: str
) -> Optional[str]:
    """
    Async version of the Genius lyrics fetching function for use with FastAPI.
    Note: lyricsgenius library is not async, so this will run synchronously.
    Consider running in a thread pool if performance becomes an issue.
    """
    try:
        # This is a synchronous call.
        # For a truly async implementation, you might need to run this in a thread pool executor.
        genius = lyricsgenius.Genius(
            settings.GENIUS_ACCESS_TOKEN,
            timeout=15,
            retries=3,
            sleep_time=0.5,
            verbose=False,
            remove_section_headers=True,
        )
        song = genius.search_song(song_title, artist_name, get_full_info=False)
        if song:
            return song.lyrics
    except Exception:
        return None


async def get_lyrics_for_song_async(song_title: str, artist_name: str) -> Optional[str]:
    """
    Try OVH first, then fall back to Genius.
    Returns lyrics string or None.
    """
    lyrics = await get_lyrics_from_ovh_async(song_title, artist_name)
    if lyrics:
        return lyrics

    if settings.GENIUS_ACCESS_TOKEN:
        return await get_lyrics_from_genius_async(song_title, artist_name)

    return None
