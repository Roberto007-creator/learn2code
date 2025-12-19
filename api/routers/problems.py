from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user
from app.schemas.problems import ProblemOut
from services.problems_service import list_problems, get_problem
from services.events_service import log_event

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("", response_model=list[ProblemOut])
def api_list_problems(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_problems(db)


@router.get("/{problem_id}", response_model=ProblemOut)
def api_get_problem(problem_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = get_problem(db, problem_id)
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")
    log_event(db, user.id, "problem_view", {"problem_id": problem_id})
    return p
