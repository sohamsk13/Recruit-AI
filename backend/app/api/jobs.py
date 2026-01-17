from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone
from ..db.mongo import db

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# ---------- Schemas ----------

class JobCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    required_skills: List[str] = Field(min_items=1)
    experience_level: str = Field(min_length=1)

class JobResponse(JobCreate):
    id: str
    created_at: datetime

# ---------- Routes ----------

@router.post("/", response_model=JobResponse)
async def create_job(job: JobCreate):
    job_doc = {
        **job.model_dump(),
        "created_at": datetime.now(timezone.utc)
    }

    result = await db.jobs.insert_one(job_doc)

    return {
        "id": str(result.inserted_id),
        **job_doc
    }


@router.get("/", response_model=List[JobResponse])
async def list_jobs(limit: int = 100, offset: int = 0):
    cursor = db.jobs.find().skip(offset).limit(limit)
    
    jobs = [
        {
            "id": str(job["_id"]),
            "title": job["title"],
            "description": job["description"],
            "required_skills": job["required_skills"],
            "experience_level": job["experience_level"],
            "created_at": job["created_at"]
        }
        async for job in cursor
    ]

    return jobs
