from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Resource not found error"""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AuthenticationError(HTTPException):
    """Authentication error"""

    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Authorization error"""

    def __init__(self, detail: str = "Not enough permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationError(HTTPException):
    """Validation error"""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ExternalAPIError(HTTPException):
    """External API error"""

    def __init__(self, detail: str = "Error communicating with external service"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class SpotifyDeviceNotFoundError(HTTPException):
    """Spotify active device not found error"""

    def __init__(self, detail: str = "Spotify active device not found. Please start playback on a Spotify device."):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
