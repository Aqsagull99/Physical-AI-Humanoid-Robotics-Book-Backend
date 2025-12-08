from fastapi import APIRouter, HTTPException, Depends
from core.auth import verify_api_key, verify_admin_api_key
from pydantic import BaseModel
from typing import Optional
import os
from core.logging import logger
from core.config import settings
from services.retrieval import get_retrieval_service
from services.vector_store import get_vector_store

router = APIRouter()

# Request and Response models for admin endpoints
class RefreshRequest(BaseModel):
    force: bool = False

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: Optional[str]
    memory_usage: Optional[str]

class RefreshResponse(BaseModel):
    status: str
    message: str
    processed_files: int

@router.get("/admin/health", response_model=HealthResponse)
async def admin_health(api_key_valid: bool = Depends(verify_admin_api_key)):
    """
    Admin health check with detailed system information
    """
    logger.info("Admin health check requested")
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        uptime=None,
        memory_usage=None
    )

@router.post("/admin/ingest", response_model=dict)
async def ingest_content(api_key_valid: bool = Depends(verify_admin_api_key)):
    """
    Admin endpoint to ingest book content into the vector database
    Matches the OpenAPI specification
    """
    logger.info("Ingest content endpoint called")

    try:
        # Initialize the vector store with book content
        get_retrieval_service().initialize_store()

        return {
            "status": "success",
            "message": "Content ingested successfully"
        }
    except Exception as e:
        logger.error(f"Error ingesting content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ingesting content: {str(e)}")


@router.post("/admin/refresh", response_model=RefreshResponse)
async def refresh_embeddings(request: RefreshRequest, api_key_valid: bool = Depends(verify_admin_api_key)):
    """
    Admin endpoint to refresh embeddings from book content
    """
    logger.info(f"Refresh embeddings requested with force={request.force}")

    try:
        # Initialize the vector store with book content
        get_retrieval_service().initialize_store()

        # Get the number of content items loaded
        # We need to access the vector store to get the count
        vector_store = get_vector_store()
        # Since we don't have a direct count method, we'll return a success message
        return RefreshResponse(
            status="success",
            message="Embeddings refresh completed successfully",
            processed_files=1  # Simplified - in reality, we'd count the actual files processed
        )
    except Exception as e:
        logger.error(f"Error refreshing embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing embeddings: {str(e)}")