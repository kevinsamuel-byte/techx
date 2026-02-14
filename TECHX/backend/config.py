from pydantic import BaseModel
import os


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./career_agent.db")
    session_ttl_hours: int = int(os.getenv("SESSION_TTL_HOURS", "336"))


settings = Settings()
