from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class HealthCheck(BaseModel):
    """Response model for health check endpoint"""
    status: str
    timestamp: str
    version: str

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint to monitor service availability"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )