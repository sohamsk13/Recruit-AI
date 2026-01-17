import requests
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from ..core.config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0
)

GITHUB_API = "https://api.github.com/users"


def fetch_repos(username: str):
    try:
        response = requests.get(f"{GITHUB_API}/{username}/repos", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch GitHub repos: {str(e)}")


async def analyze_github(username: str, job_role: str) -> dict:
    try:
        repos = fetch_repos(username)

        simplified_repos = [
            {
                "name": r.get("name", ""),
                "description": r.get("description", ""),
                "language": r.get("language", ""),
                "stars": r.get("stargazers_count", 0)
            }
            for r in repos
        ]

        prompt = f"""
        You are evaluating a GitHub profile for a {job_role} role.

        Repositories:
        {simplified_repos}

        Give:
        - GitHub skill score (0-100)
        - Tech strengths
        - Weaknesses
        - Short hiring insight

        Output JSON only with keys: github_score, tech_strengths, weaknesses, hiring_insight
        """

        response = llm.invoke(prompt)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "github_score": 0,
                "tech_strengths": [],
                "weaknesses": [],
                "hiring_insight": "Unable to analyze GitHub profile"
            }
    except Exception as e:
        return {
            "github_score": 0,
            "tech_strengths": [],
            "weaknesses": [],
            "hiring_insight": f"Error analyzing GitHub: {str(e)}"
        }
