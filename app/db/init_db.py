import json
from pathlib import Path
from sqlalchemy import select
from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.db.models import Problem


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def seed_problems_from_json(json_path: str = "data/problems.json") -> None:
    path = Path(json_path)
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as f:
        items = json.load(f)

    db = SessionLocal()
    try:
        for p in items:
            existing = db.scalar(select(Problem).where(Problem.id == p["id"]))
            if existing:
                continue
            db.add(
                Problem(
                    id=p["id"],
                    title=p["title"],
                    topic=p["topic"],
                    difficulty=p["difficulty"],
                    statement=p["statement"],
                    examples=p.get("examples", ""),
                )
            )
        db.commit()
    finally:
        db.close()
