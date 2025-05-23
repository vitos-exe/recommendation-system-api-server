from typing import List

import httpx

from app.config import settings
from app.schemas.mood import MoodBase
from app.schemas.recommendation import RecommendedSong


async def predict_mood_from_lyrics(lyrics: str, artist: str, title: str) -> MoodBase:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AI_API_URL}/",
            params={"save": "True"},
            json={"lyrics": lyrics, "artist": artist, "title": title},
        )
        response.raise_for_status()
        return MoodBase(**response.json())


async def get_recommendations_for_mood(
    mood: MoodBase, limit: int = 5
) -> List[RecommendedSong]:
    mood_dict = {
        "happy": mood.happy,
        "sad": mood.sad,
        "angry": mood.angry,
        "relaxed": mood.relaxed,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.AI_API_URL}/closest",
            params={"limit": limit},
            json=mood_dict,
        )
        response.raise_for_status()
        return [RecommendedSong(**item) for item in response.json()]
