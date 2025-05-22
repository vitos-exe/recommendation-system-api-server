from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Music Recommendation API",
    description="API server for music recommendation system based on emotional analysis",
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Music Recommendation API",
        "docs_url": "/docs",
    }
