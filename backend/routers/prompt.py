from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.prompt_history import PromptHistory
from backend.schemas.prompt import PromptRequest, PromptResponse
from backend.services.ampoa import AMPOAEngine
from backend.services.mapt import MAPTEngine
from backend.services.scoring import PromptScorer

router = APIRouter(prefix="/prompt", tags=["Prompt Optimization"])

_ampoa = AMPOAEngine()
_mapt = MAPTEngine()
_scorer = PromptScorer()


@router.post("/optimize", response_model=PromptResponse)
def optimize_prompt(
    request: PromptRequest,
    db: Session = Depends(get_db),
):
    """
    Full optimization pipeline:
      1. AMPOA  – clean, analyse and structure the raw prompt
      2. MAPT   – adapt the universal prompt for the target LLM
      3. Scorer – score the adapted prompt

    The result is persisted to the user's history and returned.
    """
    # --- AMPOA stage ---
    try:
        ampoa_result = _ampoa.optimize(request.original_prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AMPOA processing failed: {exc}",
        )

    universal_prompt: str = ampoa_result["universal_prompt"]

    # --- MAPT stage ---
    try:
        adapted_prompt = _mapt.translate(universal_prompt, request.target_llm)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MAPT translation failed: {exc}",
        )

    # --- Scoring stage ---
    try:
        quality = _scorer.score(adapted_prompt)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality scoring failed: {exc}",
        )

    quality_score: float = quality["score"]
    quality_breakdown: dict = quality

    # --- Persist to history ---
    history_entry = PromptHistory(
        session_id=request.session_id or "anonymous",
        original_prompt=request.original_prompt,
        universal_prompt=universal_prompt,
        target_llm=request.target_llm,
        adapted_prompt=adapted_prompt,
        quality_score=quality_score,
    )
    db.add(history_entry)
    db.commit()

    return PromptResponse(
        original_prompt=request.original_prompt,
        universal_prompt=universal_prompt,
        adapted_prompt=adapted_prompt,
        target_llm=request.target_llm,
        quality_score=quality_score,
        quality_breakdown=quality_breakdown,
        ampoa_stages=ampoa_result,
    )
