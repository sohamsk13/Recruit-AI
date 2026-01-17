import asyncio
from bson import ObjectId
from ..db.mongo import db
from .graph import build_graph

async def process_ai_queue():
    """Process pending AI evaluations"""
    graph = build_graph()
    
    while True:
        try:
            # Get pending job from queue
            queue_item = await db.ai_queue.find_one({"status": "pending"})
            
            if not queue_item:
                await asyncio.sleep(5)  # Wait 5 seconds before checking again
                continue
            
            # Mark as processing
            await db.ai_queue.update_one(
                {"_id": queue_item["_id"]},
                {"$set": {"status": "processing"}}
            )
            
            # Get applicant and job data
            applicant = await db.applicants.find_one({"_id": ObjectId(queue_item["applicant_id"])})
            job = await db.jobs.find_one({"_id": ObjectId(queue_item["job_id"])})
            
            if not applicant or not job:
                await db.ai_queue.update_one(
                    {"_id": queue_item["_id"]},
                    {"$set": {"status": "failed", "error": "Applicant or job not found"}}
                )
                continue
            
            # Prepare state for graph
            state = {
                "applicant_id": queue_item["applicant_id"],
                "job_id": queue_item["job_id"],
                "resume_path": applicant["resume_path"],
                "github_username": applicant.get("github_username", ""),
                "job_skills": job["required_skills"],
                "job_role": job["title"]
            }
            
            # Run AI pipeline
            await graph.ainvoke(state)
            
            # Mark as completed
            await db.ai_queue.update_one(
                {"_id": queue_item["_id"]},
                {"$set": {"status": "completed"}}
            )
            
        except Exception as e:
            print(f"Error processing queue item: {e}")
            if 'queue_item' in locals():
                await db.ai_queue.update_one(
                    {"_id": queue_item["_id"]},
                    {"$set": {"status": "failed", "error": str(e)}}
                )
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(process_ai_queue())