from pydantic import BaseModel


class StoryResponse(BaseModel):
    topic: str
    story: str
