from langgraph.graph import StateGraph,END
from typing import TypedDict, List
from datetime import datetime

from .resume_parser import parse_resume
from .github_analyzer import analyze_github
from .skill_matcher import match_skills
from ..db.mongo import db


# ---------- STATE ----------

class HiringState(TypedDict):
    applicant_id: str
    job_id: str
    resume_path: str
    github_username: str
    job_skills: List[str]
    job_role: str

    resume_data: dict
    skill_match_result: dict     # ✅ renamed
    github_data: dict
    final_score: int
    decision: str


# ---------- NODES ----------

async def resume_node(state: HiringState):
    try:
        state["resume_data"] = await parse_resume(state["resume_path"])
    except Exception as e:
        print("Resume parsing failed:", e)
        state["resume_data"] = {"skills": []}
    return state


async def skill_match_node(state: HiringState):
    try:
        resume_skills = state.get("resume_data", {}).get("skills", [])
        state["skill_match_result"] = match_skills(
            state["job_skills"],
            resume_skills
        )
    except Exception as e:
        print("Skill matching failed:", e)
        state["skill_match_result"] = {"skill_match_score": 0}
    return state


async def github_node(state: HiringState):
    try:
        state["github_data"] = await analyze_github(
            state["github_username"]    # ✅ FIXED
        )
    except Exception as e:
        print("GitHub analysis failed:", e)
        state["github_data"] = {
            "github_score": 0,
            "hiring_insight": "GitHub analysis failed"
        }
    return state


async def decision_node(state: HiringState):
    try:
        skill_score = state.get("skill_match_result", {}).get("skill_match_score", 0)
        github_score = state.get("github_data", {}).get("github_score", 0)

        final_score = int(skill_score * 0.6 + github_score * 0.4)

        decision = (
            "Strong Match" if final_score >= 75 else
            "Moderate Match" if final_score >= 50 else
            "Weak Match"
        )

        hiring_insight = state.get("github_data", {}).get(
            "hiring_insight",
            "No insight available"
        )

        await db.evaluations.insert_one({
            "applicant_id": state["applicant_id"],
            "job_id": state["job_id"],
            "final_score": final_score,
            "decision": decision,
            "ai_summary": hiring_insight,
            "created_at": datetime.utcnow()
        })

        state["final_score"] = final_score
        state["decision"] = decision

    except Exception as e:
        print("Decision node failed:", e)

    return state


# ---------- GRAPH ----------

def build_graph():
    graph = StateGraph(HiringState)

    graph.add_node("resume_parser", resume_node)
    graph.add_node("skill_matcher", skill_match_node)   # ✅ renamed
    graph.add_node("github_analyzer", github_node)
    graph.add_node("decision_maker", decision_node)

    graph.set_entry_point("resume_parser")
    graph.add_edge("resume_parser", "skill_matcher")
    graph.add_edge("skill_matcher", "github_analyzer")
    graph.add_edge("github_analyzer", "decision_maker")
    graph.add_edge("decision_maker", END)  

    return graph.compile()
