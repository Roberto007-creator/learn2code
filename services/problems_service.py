from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Problem


def list_problems(db: Session) -> list[Problem]:
    return list(db.scalars(select(Problem).order_by(Problem.difficulty, Problem.topic, Problem.title)))


def get_problem(db: Session, problem_id: str) -> Problem | None:
    return db.scalar(select(Problem).where(Problem.id == problem_id))
