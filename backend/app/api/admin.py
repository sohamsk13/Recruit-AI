from fastapi import APIRouter, HTTPException
from typing import List
from bson import ObjectId
from ..db.mongo import db

router = APIRouter(prefix="/admin", tags=["Admin"])

# ---------- Routes ----------

@router.get("/candidates/{job_id}")
async def get_candidates_for_job(job_id: str):
    try:
        object_id = ObjectId(job_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    job = await db.jobs.find_one({"_id": object_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    pipeline = [
        {"$match": {"job_id": job_id}},
        {"$lookup": {
            "from": "evaluations",
            "localField": "_id",
            "foreignField": "applicant_id",
            "as": "evaluation"
        }},
        {"$addFields": {
            "applicant_id_str": {"$toString": "$_id"}
        }},
        {"$lookup": {
            "from": "evaluations",
            "localField": "applicant_id_str",
            "foreignField": "applicant_id",
            "as": "evaluation"
        }},
        {"$unwind": {"path": "$evaluation", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"evaluation.final_score": -1}}
    ]

    results = [
        {
            "applicant_id": str(doc["_id"]),
            "name": doc.get("name"),
            "email": doc.get("email"),
            "github_url": doc.get("github_url"),
            "final_score": doc.get("evaluation", {}).get("final_score"),
            "decision": doc.get("evaluation", {}).get("decision"),
            "ai_summary": doc.get("evaluation", {}).get("ai_summary")
        }
        async for doc in db.applicants.aggregate(pipeline)
    ]

    return {
        "job_title": job.get("title"),
        "candidates": results
    }
