from sqlalchemy.orm import Session
from agents.base import BaseAgent, AgentResult
from agents.llm import LLMMessage
from agents.prompts import NAVIGATOR_SYSTEM
from services.stats_service import topic_stats


class ProgressNavigatorAgent(BaseAgent):
    name = "progress_navigator"

    def __init__(self, llm_client):
        self.llm = llm_client

    def run(self, db: Session, user_id: int) -> AgentResult:
        rows = topic_stats(db, user_id)

        computed = []
        for r in rows:
            attempts = int(r.attempts or 0)
            solved = int(r.solved or 0)
            avg_time = int(r.avg_time or 0)
            avg_errors = float(r.avg_errors or 0.0)

            error_rate = min(1.0, avg_errors / 5.0) if attempts else 0.0
            mastery = (solved / attempts) if attempts else 0.0

            computed.append(
                {
                    "topic": r.topic,
                    "attempts": attempts,
                    "solved": solved,
                    "avg_time_sec": avg_time,
                    "error_rate": round(error_rate, 3),
                    "mastery": round(mastery, 3),
                }
            )

        weak_topics = [x["topic"] for x in sorted(computed, key=lambda t: (t["mastery"], -t["attempts"]))[:3]]

        llm_text = self.llm.chat(
            [
                LLMMessage(role="system", content=NAVIGATOR_SYSTEM),
                LLMMessage(
                    role="user",
                    content=f"Статистика по темам:\n{computed}\n\nСформируй план на 7 дней.",
                ),
            ]
        )

        return AgentResult(
            ok=True,
            payload={
                "weak_topics": weak_topics,
                "recommendations_text": llm_text,
                "topic_stats": computed,
            },
            debug=None,
        )
