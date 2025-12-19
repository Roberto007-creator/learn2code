from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.deps import get_db, get_current_user
from app.schemas.submissions import SubmissionCreateIn, SubmissionOut, SubmissionStatusIn
from app.services.submissions_service import create_submission, list_user_submissions, set_submission_status
from app.services.problems_service import get_problem
from app.services.events_service import log_event
from app.db.models import Submission

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionOut)
def api_submit(payload: SubmissionCreateIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    p = get_problem(db, payload.problem_id)
    if not p:
        raise HTTPException(status_code=404, detail="Problem not found")

    sub = create_submission(
        db=db,
        user_id=user.id,
        problem_id=payload.problem_id,
        language=payload.language,
        code=payload.code,
        time_spent_sec=payload.time_spent_sec,
    )
    log_event(db, user.id, "submission_created", {"problem_id": payload.problem_id, "submission_id": sub.id})
    return sub


@router.get("", response_model=list[SubmissionOut])
def api_list_my(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_user_submissions(db, user.id)


@router.post("/{submission_id}/set_status", response_model=SubmissionOut)
def api_set_status(
    submission_id: int,
    payload: SubmissionStatusIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sub = db.scalar(select(Submission).where(Submission.id == submission_id, Submission.user_id == user.id))
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    try:
        sub = set_submission_status(db, sub, payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Bad status")

    log_event(db, user.id, "submission_status_changed", {"submission_id": sub.id, "status": sub.status})
    return sub
