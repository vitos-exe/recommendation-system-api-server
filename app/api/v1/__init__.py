from fastapi import APIRouter

from app.api.v1.endpoints import auth, mood, recommendations, spotify, users

api_router = APIRouter()

# Include all router endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(spotify.router, prefix="/spotify", tags=["spotify"])
api_router.include_router(mood.router, prefix="/mood", tags=["mood"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["recommendations"]
)
