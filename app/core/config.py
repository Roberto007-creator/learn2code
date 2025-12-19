from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"

    jwt_secret: str = "change_me_please"
    jwt_alg: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    llm_base_url: str = "https://api.openai.com"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
