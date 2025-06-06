from datetime import datetime, timedelta
from typing import Any, Optional, Union

from jose import jwt
from passlib.context import CryptContext

from app.config import settings, logger  # Modified import

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT token with an expiration time
    """
    logger.debug(f"Creating access token for subject: {subject}")
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        logger.debug(f"Using default token expiry of {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"JWT token created successfully, expires: {expire}")
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    logger.debug("Verifying password against hash")
    result = pwd_context.verify(plain_password, hashed_password)
    if not result:
        logger.debug("Password verification failed")
    return result


def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    logger.debug("Hashing password")
    hashed = pwd_context.hash(password)
    logger.debug("Password hashed successfully")
    return hashed
