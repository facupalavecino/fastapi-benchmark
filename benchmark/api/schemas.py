import enum
from pydantic import BaseModel


class StoryResponse(BaseModel):
    topic: str
    story: str


class StorytellerModel(enum.Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4O_MINI = "gpt-4o-mini"
    BEDROCK_CLAUDE_SONNET = "anthropic.claude-3-5-sonnet-20240620-v1:0"
