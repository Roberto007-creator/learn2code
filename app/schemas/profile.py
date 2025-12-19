from pydantic import BaseModel


class TopicStat(BaseModel):
    topic: str
    attempts: int
    solved: int
    avg_time_sec: int
    error_rate: float
    mastery: float


class ProfileOut(BaseModel):
    username: str
    total_attempts: int
    total_solved: int
    topics: list[TopicStat]
    recommendations: list[str]
