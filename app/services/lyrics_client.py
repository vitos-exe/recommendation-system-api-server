import re
from typing import Optional

import httpx

OVH_LYRICS_API_URL = "https://api.lyrics.ovh/v1"


async def get_lyrics_for_song_async(song_title: str, artist_name: str) -> Optional[str]:
    """
    Async version of the lyrics fetching function for use with FastAPI
    """
    # httpx can be used for async requests directly
    url = f"{OVH_LYRICS_API_URL}/{artist_name}/{song_title}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            lyrics = data.get("lyrics")

        if lyrics:
            # Clean up lyrics
            lyrics = re.sub(r"\n{2,}", "\n", lyrics)
            lyrics = re.sub(r"\r\n", "\n", lyrics)
            lyrics = "\n".join(
                [line.strip() for line in lyrics.split("\n") if line.strip()]
            )
            return lyrics
        return None
    except httpx.HTTPStatusError as err:
        print(f"OVH async request failed: {err}")
    except ValueError as err:
        print(f"Invalid JSON response from OVH (async): {err}")
    except httpx.RequestError as err:
        print(f"OVH async request error: {err}")
    except Exception as e:
        print(f"Error processing lyrics (async): {e}")
    return None
