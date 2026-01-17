from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "ai_hiring"
    GEMINI_API_KEY: str
    GITHUB_TOKEN: str
    RESUME_UPLOAD_DIR: str = "uploads/resumes"
    
    class Config:
        env_file = ".env"

settings = Settings()
