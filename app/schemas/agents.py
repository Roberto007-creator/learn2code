from pydantic import BaseModel


class ReviewOut(BaseModel):
    summary: str
    details: str
    score_readability: int
    score_correctness: int
    score_efficiency: int


class MentorHintOut(BaseModel):
    hints: list[str]
    explanation: str


class NavigatorOut(BaseModel):
    recommendations: list[str]
    weak_topics: list[str]
