\
# filepath: /Users/vitalii.chernysh/final-paper/recommendation-system-api-server/app/schemas/recommendation.py
from pydantic import BaseModel
from typing import Dict

class MoodPrediction(BaseModel):
    angry: float
    happy: float
    relaxed: float
    sad: float

class RecommendedSong(BaseModel):
    artist: str
    title: str
    prediction: MoodPrediction
