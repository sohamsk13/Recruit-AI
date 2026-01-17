#!/usr/bin/env python3
"""
Startup script for AI Hiring Platform
"""
import asyncio
import uvicorn
from app.main import app
from app.ai.process_queue import process_ai_queue
from app.core.logging_config import setup_logging

# Setup logging
logger = setup_logging()

async def start_background_tasks():
    """Start background AI processing"""
    logger.info("Starting background AI processing task")
    asyncio.create_task(process_ai_queue())

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    logger.info("Starting AI Hiring Platform")
    await start_background_tasks()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Hiring Platform")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )