# filepath: /Users/vitalii.chernysh/final-paper/recommendation-system-api-server/app/schemas/recommendation.py

from pydantic import BaseModel

from app.schemas.mood import MoodBase  # Import MoodBase


class RecommendedSong(BaseModel):
    artist: str
    title: str
    prediction: MoodBase  # Use MoodBase here
