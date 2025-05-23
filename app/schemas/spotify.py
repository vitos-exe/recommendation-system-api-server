from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SpotifyAuth(BaseModel):
    auth_url: str
    state: str


class SpotifyAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


class SpotifyTrack(BaseModel):
    id: str
    name: str
    artist: str
    album: str
    uri: Optional[str] = None
    played_at: Optional[datetime] = None
    preview_url: Optional[str] = None


class SpotifyRecommendation(BaseModel):
    tracks: List[SpotifyTrack]
