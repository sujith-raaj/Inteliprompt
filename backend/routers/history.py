from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.prompt_history import PromptHistory
from backend.schemas.prompt import HistoryItem

router = APIRouter(prefix="/history", tags=["Prompt History"])


@router.get("/", response_model=List[HistoryItem])
def get_history(
    session_id: str = Query(default="anonymous"),
    db: Session = Depends(get_db),
):
    """Return prompt history entries for the given session, newest first."""
    return (
        db.query(PromptHistory)
        .filter(PromptHistory.session_id == session_id)
        .order_by(PromptHistory.created_at.desc())
        .limit(50)
        .all()
    )


@router.delete("/{item_id}")
def delete_history_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """Delete a specific history entry by ID."""
    entry = db.query(PromptHistory).filter(PromptHistory.id == item_id).first()
    if entry:
        db.delete(entry)
        db.commit()
    return {"status": "deleted"}
