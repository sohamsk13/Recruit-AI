from fastapi import APIRouter, HTTPException
from ..db.mongo import db
from ..core.config import settings
import asyncio

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "AI Hiring Platform"}

@router.get("/db")
async def database_health():
    """Database connectivity check"""
    try:
        # Test database connection
        await db.command("ping")
        
        # Get collection stats
        jobs_count = await db.jobs.count_documents({})
        applicants_count = await db.applicants.count_documents({})
        
        return {
            "status": "healthy",
            "database": "connected",
            "collections": {
                "jobs": jobs_count,
                "applicants": applicants_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")

@router.get("/ai")
async def ai_services_health():
    """AI services health check"""
    try:
        # Check if Gemini API key is configured
        if not settings.GEMINI_API_KEY:
            raise Exception("Gemini API key not configured")
        
        # Check AI queue status
        pending_jobs = await db.ai_queue.count_documents({"status": "pending"})
        processing_jobs = await db.ai_queue.count_documents({"status": "processing"})
        
        return {
            "status": "healthy",
            "gemini_api": "configured",
            "ai_queue": {
                "pending": pending_jobs,
                "processing": processing_jobs
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI services unhealthy: {str(e)}")