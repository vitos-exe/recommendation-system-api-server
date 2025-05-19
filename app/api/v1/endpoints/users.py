from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.schemas.user import UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def get_user_me(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserSchema)
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update current user profile"""
    if user_in.password:
        from app.services.auth.jwt import get_password_hash

        current_user.hashed_password = get_password_hash(user_in.password)
    if user_in.email:
        current_user.email = user_in.email

    db.commit()
    db.refresh(current_user)
    return current_user
