from fastapi import HTTPException, Header, status
from core.config import settings
from core.logging import logger

def verify_api_key(api_key: str = Header(None, alias="X-API-Key")):
    """
    Verify the API key from the request header for regular endpoints
    If no API key is required (settings.api_key is None), allow access
    """
    if not settings.api_key:
        # If no API key is configured, allow access (development mode)
        return True

    if not api_key or api_key != settings.api_key:
        logger.warning("Invalid or missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )

    return True

def verify_admin_api_key(api_key: str = Header(None, alias="X-API-Key")):
    """
    Verify the admin API key from the request header
    If no admin API key is required (settings.admin_api_key is None), allow access
    """
    if not settings.admin_api_key:
        # If no admin API key is configured, allow access (development mode)
        return True

    if not api_key or api_key != settings.admin_api_key:
        logger.warning("Invalid or missing admin API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key"
        )

    return True