from fastapi import Depends, HTTPException, Header
from app.config.settings import API_KEY


async def verify_api_key(x_api_key: str = Header(..., description="API Key")):
    """
    Verify API key from request header.
    Header: X-API-Key
    """
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API_KEY not configured in environment"
        )
    
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return x_api_key
