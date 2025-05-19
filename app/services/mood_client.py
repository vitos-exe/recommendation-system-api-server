from typing import Dict, List

import httpx

from app.config import settings


async def predict_mood_from_lyrics(
    lyrics: str, artist: str, title: str
) -> Dict[str, float]:
    """
    Use the AI API to predict the emotional mood from song lyrics

    Returns a dictionary with probabilities for each emotion:
    {
        "happy": 0.7,
        "sad": 0.1,
        "angry": 0.05,
        "relaxed": 0.15
    }
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AI_API_URL}/",  # Changed endpoint
                json={"lyrics": lyrics, "artist": artist, "title": title},
            )

            if response.status_code != 200:
                print(f"Error from AI API: {response.text}")
                # Return default values if the API call fails
                return {"happy": 0.25, "sad": 0.25, "angry": 0.25, "relaxed": 0.25}

            data = response.json()
            return data  # Changed: assume response is the mood probability dict
    except Exception as e:
        print(f"Error predicting mood: {e}")
        # Return default values if the API call fails
        return {"happy": 0.25, "sad": 0.25, "angry": 0.25, "relaxed": 0.25}


async def get_recommendations_for_mood(
    mood_vector: Dict[str, float], limit: int = 5
) -> List[Dict[str, str]]:
    """
    Get song recommendations based on a mood vector

    The AI service should return songs from its vector database that match the given mood
    Note: The 'limit' parameter is part of this client function, but the current AI service
    endpoint (/closest) is configured to return a fixed number of results (n=1).
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.AI_API_URL}/closest",  # Changed endpoint
                json=mood_vector,  # Changed: send mood_vector directly
            )

            if response.status_code != 200:
                print(f"Error from AI API: {response.text}")
                return []

            data = response.json()
            return data  # Changed: assume response is the list of recommendations
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []


def average_mood_vectors(mood_vectors: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calculate the average mood vector from a list of mood vectors
    """
    if not mood_vectors:
        return {"happy": 0.25, "sad": 0.25, "angry": 0.25, "relaxed": 0.25}

    result = {"happy": 0.0, "sad": 0.0, "angry": 0.0, "relaxed": 0.0}
    count = len(mood_vectors)

    for vector in mood_vectors:
        for mood, value in vector.items():
            result[mood] += value

    for mood in result:
        result[mood] /= count

    return result
