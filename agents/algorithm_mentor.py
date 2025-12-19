from app.agents.base import BaseAgent, AgentResult
from app.agents.llm import LLMMessage
from app.agents.prompts import MENTOR_SYSTEM


class AlgorithmMentorAgent(BaseAgent):
    name = "algorithm_mentor"

    def __init__(self, llm_client):
        self.llm = llm_client

    def run(self, problem_statement: str, examples: str, user_attempt: str | None = None) -> AgentResult:
        user_part = f"\nПопытка пользователя:\n{user_attempt}\n" if user_attempt else ""
        text = self.llm.chat(
            [
                LLMMessage(role="system", content=MENTOR_SYSTEM),
                LLMMessage(role="user", content=f"Условие:\n{problem_statement}\n\nПримеры:\n{examples}\n{user_part}"),
            ]
        )
        return AgentResult(ok=True, payload={"hints_text": text}, debug=None)
