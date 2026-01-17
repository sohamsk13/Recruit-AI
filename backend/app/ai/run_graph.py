import asyncio
from app.ai.graph import build_graph

async def run():
    graph = build_graph()

    await graph.ainvoke({
        "applicant_id": "TEST_ID",
        "job_id": "JOB_ID",
        "resume_path": "uploads/resumes/test.pdf",
        "github_username": "octocat",
        "job_skills": ["Python", "FastAPI"],
        "job_role": "Backend Engineer"
    })

asyncio.run(run())
