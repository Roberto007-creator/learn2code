from pydantic import BaseModel


class EventOut(BaseModel):
    event_type: str
    payload_json: str

    class Config:
        from_attributes = True
