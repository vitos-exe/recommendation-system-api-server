from typing import Optional

import httpx
import lyricsgenius

from app.config import settings, logger  # Modified import

OVH_LYRICS_API_URL = "https://api.lyrics.ovh/v1"


async def get_lyrics_from_ovh_async(song_title: str, artist_name: str) -> Optional[str]:
    """
    Async version of the OVH lyrics fetching function for use with FastAPI
    """
    logger.info(f"Fetching lyrics from OVH for '{song_title}' by '{artist_name}'")
    url = f"{OVH_LYRICS_API_URL}/{artist_name}/{song_title}"
    try:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending request to OVH API: {url}")
            resp = await client.get(url, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            lyrics = data.get("lyrics")
            if lyrics:
                logger.info(f"Successfully retrieved lyrics from OVH for '{song_title}' by '{artist_name}'")
                return lyrics
            else:
                logger.warning(f"OVH returned empty lyrics for '{song_title}' by '{artist_name}'")
                return None
    except Exception as e:
        logger.error(f"Error fetching lyrics from OVH for '{song_title}' by '{artist_name}': {str(e)}")
        return None


async def get_lyrics_from_genius_async(
    song_title: str, artist_name: str
) -> Optional[str]:
    """
    Async version of the Genius lyrics fetching function for use with FastAPI.
    Note: lyricsgenius library is not async, so this will run synchronously.
    Consider running in a thread pool if performance becomes an issue.
    """
    logger.info(f"Fetching lyrics from Genius for '{song_title}' by '{artist_name}'")
    if not settings.GENIUS_ACCESS_TOKEN:
        logger.warning("No Genius API token configured, skipping Genius lyrics fetch")
        return None
    
    try:
        # This is a synchronous call.
        # For a truly async implementation, you might need to run this in a thread pool executor.
        logger.debug("Initializing Genius client")
        genius = lyricsgenius.Genius(
            settings.GENIUS_ACCESS_TOKEN,
            timeout=15,
            retries=3,
            sleep_time=0.5,
            verbose=False,
            remove_section_headers=True,
        )
        logger.debug(f"Searching for song: '{song_title}' by '{artist_name}'")
        song = genius.search_song(song_title, artist_name, get_full_info=False)
        if song:
            logger.info(f"Successfully retrieved lyrics from Genius for '{song_title}' by '{artist_name}'")
            return song.lyrics
        else:
            logger.warning(f"Song not found on Genius: '{song_title}' by '{artist_name}'")
            return None
    except Exception as e:
        logger.error(f"Error fetching lyrics from Genius for '{song_title}' by '{artist_name}': {str(e)}")
        return None


async def get_lyrics_for_song_async(song_title: str, artist_name: str) -> Optional[str]:
    """
    Try OVH first, then fall back to Genius.
    Returns lyrics string or None.
    """
    logger.info(f"Attempting to get lyrics for '{song_title}' by '{artist_name}'")
    
    # Try OVH first
    lyrics = await get_lyrics_from_ovh_async(song_title, artist_name)
    if lyrics:
        logger.debug(f"Using lyrics from OVH for '{song_title}' by '{artist_name}'")
        return lyrics

    # Fall back to Genius if available
    if settings.GENIUS_ACCESS_TOKEN:
        logger.debug(f"OVH failed, trying Genius for '{song_title}' by '{artist_name}'")
        lyrics = await get_lyrics_from_genius_async(song_title, artist_name)
        if lyrics:
            return lyrics
    
    logger.warning(f"Failed to get lyrics from any source for '{song_title}' by '{artist_name}'")
    return None
