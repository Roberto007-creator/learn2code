from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Submission


def create_submission(
    db: Session,
    user_id: int,
    problem_id: str,
    language: str,
    code: str,
    time_spent_sec: int = 0,
) -> Submission:
    sub = Submission(
        user_id=user_id,
        problem_id=problem_id,
        language=language,
        code=code,
        time_spent_sec=time_spent_sec,
        status="submitted",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def list_user_submissions(db: Session, user_id: int, limit: int = 50) -> list[Submission]:
    stmt = select(Submission).where(Submission.user_id == user_id).order_by(Submission.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def set_submission_status(db: Session, submission: Submission, status: str) -> Submission:
    if status not in {"submitted", "accepted", "rejected"}:
        raise ValueError("bad status")
    submission.status = status
    db.commit()
    db.refresh(submission)
    return submission
