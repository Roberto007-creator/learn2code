from sqlalchemy import select, func, case
from sqlalchemy.orm import Session
from app.db.models import Submission, Problem


def get_user_totals(db: Session, user_id: int) -> tuple[int, int]:
    total_attempts = db.scalar(select(func.count()).select_from(Submission).where(Submission.user_id == user_id)) or 0
    total_solved = (
            db.scalar(
                select(func.count())
                .select_from(Submission)
                .where(Submission.user_id == user_id, Submission.status == "accepted")
            )
            or 0
    )
    return int(total_attempts), int(total_solved)


def topic_stats(db: Session, user_id: int):
    solved_case = case((Submission.status == "accepted", 1), else_=0)
    stmt = (
        select(
            Problem.topic.label("topic"),
            func.count(Submission.id).label("attempts"),
            func.sum(solved_case).label("solved"),
            func.avg(Submission.time_spent_sec).label("avg_time"),
            func.avg(Submission.error_count).label("avg_errors"),
        )
        .join(Problem, Problem.id == Submission.problem_id)
        .where(Submission.user_id == user_id)
        .group_by(Problem.topic)
        .order_by(Problem.topic)
    )
    rows = db.execute(stmt).all()
    return rows
