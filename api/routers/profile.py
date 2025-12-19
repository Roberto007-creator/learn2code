from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.profile import ProfileOut, TopicStat
from app.services.stats_service import get_user_totals, topic_stats

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def api_profile(db: Session = Depends(get_db), user=Depends(get_current_user)):
    total_attempts, total_solved = get_user_totals(db, user.id)

    rows = topic_stats(db, user.id)
    topics = []
    for r in rows:
        attempts = int(r.attempts or 0)
        solved = int(r.solved or 0)
        avg_time = int(r.avg_time or 0)
        avg_errors = float(r.avg_errors or 0.0)

        error_rate = min(1.0, avg_errors / 5.0) if attempts else 0.0
        mastery = (solved / attempts) if attempts else 0.0

        topics.append(
            TopicStat(
                topic=r.topic,
                attempts=attempts,
                solved=solved,
                avg_time_sec=avg_time,
                error_rate=round(error_rate, 3),
                mastery=round(mastery, 3),
            )
        )

    weak = [t.topic for t in sorted(topics, key=lambda x: x.mastery)[:3]]
    recs = [f"Повтори тему: {w}" for w in weak] if weak else ["Добавь 5–10 сабмитов, чтобы прогресс стал заметен."]

    return ProfileOut(
        username=user.username,
        total_attempts=total_attempts,
        total_solved=total_solved,
        topics=topics,
        recommendations=recs,
    )
