from dataclasses import dataclass
import requests


@dataclass
class LLMMessage:
    role: str
    content: str


class DummyLLMClient:
    def chat(self, messages: list[LLMMessage]) -> str:
        user_text = "\n".join([m.content for m in messages if m.role == "user"])
        return (
            "LLM отключён (Dummy режим).\n\n"
            "Запрос:\n"
            f"{user_text[:1200]}\n\n"
            "Подключи LLM_API_KEY, чтобы получать полноценные ответы."
        )


class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[LLMMessage]) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0.2,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
