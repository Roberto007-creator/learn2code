from dataclasses import dataclass


@dataclass
class AgentResult:
    ok: bool
    payload: dict
    debug: dict | None = None


class BaseAgent:
    name: str = "base"

    def run(self, *args, **kwargs) -> AgentResult:
        raise NotImplementedError
