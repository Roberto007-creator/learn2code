from pydantic import BaseModel, Field


class SubmissionCreateIn(BaseModel):
    problem_id: str
    language: str = "python"
    code: str = Field(min_length=1)
    time_spent_sec: int = 0


class SubmissionStatusIn(BaseModel):
    status: str  # accepted/rejected/submitted


class SubmissionOut(BaseModel):
    id: int
    problem_id: str
    language: str
    status: str
    time_spent_sec: int
    error_count: int
    had_edge_case_issue: bool

    class Config:
        from_attributes = True
