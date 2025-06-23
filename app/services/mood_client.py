from typing import List

import httpx

from app.config import settings, logger
from app.schemas.mood import MoodBase
from app.schemas.recommendation import RecommendedSong


async def predict_mood_from_lyrics(lyrics: str, artist: str, title: str) -> MoodBase:
    logger.info(f"Predicting mood for song: '{title}' by '{artist}'")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AI_API_URL}/prediction",
                params={"save": "True"},
                json=[{"lyrics": lyrics, "artist": artist, "title": title}],
            )
            response.raise_for_status()
            result = response.json()
            mood = MoodBase(**result[0])
            logger.info(f"Mood prediction successful for '{title}' by '{artist}': happy={mood.happy:.2f}, sad={mood.sad:.2f}, angry={mood.angry:.2f}, relaxed={mood.relaxed:.2f}")
            return mood
    except Exception as e:
        logger.error(f"Error predicting mood for '{title}' by '{artist}': {str(e)}")
        raise


async def get_recommendations_for_mood(
    mood: MoodBase, limit: int = 5
) -> List[RecommendedSong]:
    logger.info(f"Getting {limit} song recommendations for mood: happy={mood.happy:.2f}, sad={mood.sad:.2f}, angry={mood.angry:.2f}, relaxed={mood.relaxed:.2f}")
    
    mood_dict = {
        "happy": mood.happy,
        "sad": mood.sad,
        "angry": mood.angry,
        "relaxed": mood.relaxed,
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AI_API_URL}/closest",
                params={"limit": limit},
                json=mood_dict,
            )
            response.raise_for_status()
            json_result = response.json()
            recommendations = [RecommendedSong(**item) for item in json_result]
            logger.info(f"Received {len(recommendations)} song recommendations")
            return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations for mood: {str(e)}")
        raise
