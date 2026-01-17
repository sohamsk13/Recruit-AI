"""
Database initialization and health check
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

async def init_database():
    """Initialize database collections and indexes"""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    
    try:
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Create indexes for better performance
        await db.jobs.create_index("created_at")
        await db.applicants.create_index([("job_id", 1), ("created_at", -1)])
        await db.evaluations.create_index("applicant_id")
        await db.ai_queue.create_index([("status", 1), ("created_at", 1)])
        
        print("✅ Database indexes created")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"📊 Available collections: {collections}")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(init_database())