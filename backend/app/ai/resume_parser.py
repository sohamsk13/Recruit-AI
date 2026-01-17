import pdfplumber
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from ..core.config import settings

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0
)

def extract_text_from_pdf(file_path: str) -> str:
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


async def parse_resume(resume_path: str) -> dict:
    try:
        resume_text = extract_text_from_pdf(resume_path)

        prompt = f"""
        You are a hiring AI.
        Extract the following from resume text:
        - Skills (list)
        - Years of experience
        - Primary role
        - Tech stack

        Resume:
        {resume_text}

        Output strictly in JSON format.
        """

        response = llm.invoke(prompt)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "skills": [],
                "years_of_experience": 0,
                "primary_role": "Unknown",
                "tech_stack": []
            }
    except Exception as e:
        raise Exception(f"Failed to parse resume: {str(e)}")
