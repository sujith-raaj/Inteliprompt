from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from backend.database import Base

class PromptHistory(Base):
    __tablename__ = "prompt_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)  # browser session id
    original_prompt = Column(Text)
    universal_prompt = Column(Text)
    target_llm = Column(String)
    adapted_prompt = Column(Text)
    quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
