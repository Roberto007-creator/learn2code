from pydantic import BaseModel


class ProblemOut(BaseModel):
    id: str
    title: str
    topic: str
    difficulty: str
    statement: str
    examples: str

    class Config:
        from_attributes = True
