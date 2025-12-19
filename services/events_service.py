import json
from sqlalchemy.orm import Session
from app.db.models import LearningEvent


def log_event(db: Session, user_id: int, event_type: str, payload: dict | None = None) -> None:
    payload = payload or {}
    ev = LearningEvent(user_id=user_id, event_type=event_type, payload_json=json.dumps(payload, ensure_ascii=False))
    db.add(ev)
    db.commit()
