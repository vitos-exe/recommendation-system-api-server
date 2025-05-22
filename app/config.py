import os
from typing import List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:4200"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if not v.strip():
                return []
            # Split the string by commas and strip whitespace from each part,
            # filtering out any empty strings that might result from consecutive commas
            # or trailing/leading commas.
            return [item.strip() for item in v.split(",") if item.strip()]
        raise ValueError(
            f"Invalid type for BACKEND_CORS_ORIGINS: expected str or list, got {type(v)}"
        )

    DATABASE_URI: Optional[str] = None

    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    SPOTIFY_REDIRECT_URI: Optional[str] = None

    AI_API_URL: str = "http://localhost:5000"

    FRONTEND_URL: str = "http://localhost:4200"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()