from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    original_prompt: str = Field(..., min_length=5, max_length=5000)
    target_llm: Literal["claude", "chatgpt", "gemini", "deepseek"]
    session_id: Optional[str] = "anonymous"


class PromptResponse(BaseModel):
    original_prompt: str
    universal_prompt: str
    adapted_prompt: str
    target_llm: str
    quality_score: float
    quality_breakdown: dict
    ampoa_stages: dict

    model_config = {"from_attributes": True}


class HistoryItem(BaseModel):
    id: int
    session_id: str
    original_prompt: str
    universal_prompt: str
    target_llm: str
    adapted_prompt: str
    quality_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
