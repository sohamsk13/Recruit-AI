from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from datetime import datetime, timezone
import os
import uuid
from werkzeug.utils import secure_filename
from bson import ObjectId
import asyncio

from ..db.mongo import db
from ..core.config import settings
from ..ai.graph import build_graph

router = APIRouter(prefix="/apply", tags=["Applicants"])

os.makedirs(settings.RESUME_UPLOAD_DIR, exist_ok=True)

# ---------- Helpers ----------

def extract_github_username(github_url: str) -> str:
    if not github_url:
        return ""
    if "github.com/" in github_url:
        return github_url.split("github.com/")[-1].split("/")[0]
    return github_url


async def run_ai_pipeline(
    applicant_id: str,
    job_id: str,
    resume_path: str,
    github_username: str
):
    """
    Background AI evaluation pipeline
    """
    try:
        applicant_object_id = ObjectId(applicant_id)
        job_object_id = ObjectId(job_id)

        applicant = await db.applicants.find_one({"_id": applicant_object_id})
        job = await db.jobs.find_one({"_id": job_object_id})

        if not applicant or not job:
            raise Exception("Applicant or Job not found")

        graph = build_graph()

        await graph.ainvoke({
            "applicant_id": applicant_id,
            "job_id": job_id,
            "resume_path": resume_path,
            "github_username": github_username,
            "job_skills": job["required_skills"],
            "job_role": job["title"]
        })

        # Mark queue completed
        await db.ai_queue.update_one(
            {"applicant_id": applicant_id},
            {"$set": {"status": "completed", "updated_at": datetime.now(timezone.utc)}}
        )

    except Exception as e:
        # Mark queue failed
        await db.ai_queue.update_one(
            {"applicant_id": applicant_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )


# ---------- Route ----------

@router.post("/{job_id}")
async def apply_for_job(
    job_id: str,
    name: str = Form(...),
    email: str = Form(...),
    github_url: str = Form(...),
    resume: UploadFile = File(...)
):
    # Validate Job ID
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job_object_id = ObjectId(job_id)
    job = await db.jobs.find_one({"_id": job_object_id})

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Validate resume
    if not resume.filename or "." not in resume.filename:
        raise HTTPException(status_code=400, detail="Invalid resume filename")

    allowed_extensions = {"pdf", "doc", "docx"}
    file_ext = resume.filename.split(".")[-1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOC, DOCX files allowed"
        )

    # Save resume
    try:
        secure_name = secure_filename(resume.filename)
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(settings.RESUME_UPLOAD_DIR, file_name)

        with open(file_path, "wb") as f:
            f.write(await resume.read())
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to save resume")

    github_username = extract_github_username(github_url)

    applicant_doc = {
        "job_id": job_id,
        "name": name,
        "email": email,
        "github_url": github_url,
        "github_username": github_username,
        "resume_path": file_path,
        "created_at": datetime.now(timezone.utc),
        "status": "submitted"
    }

    result = await db.applicants.insert_one(applicant_doc)

    # Insert AI queue entry
    await db.ai_queue.insert_one({
        "applicant_id": str(result.inserted_id),
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    })


    def run_ai_pipeline_sync(*args, **kwargs):
        asyncio.run(run_ai_pipeline(*args, **kwargs))

    # 🚀 Trigger AI evaluation in background
    asyncio.create_task(
        run_ai_pipeline(
            applicant_id=str(result.inserted_id),
            job_id=job_id,
            resume_path=file_path,
            github_username=github_username
        )
    )
    return {
        "message": "Application submitted successfully. AI evaluation in progress.",
        "applicant_id": str(result.inserted_id)
    }
