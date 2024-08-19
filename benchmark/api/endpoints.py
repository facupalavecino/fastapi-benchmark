import logging
from typing import Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from opentelemetry import trace

from benchmark.api.schemas import StoryResponse, StorytellerModel
from benchmark.llms.bedrock import ClaudeBedrockLlm
from benchmark.llms.gpt import OpenAILlm


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()

tracer: trace.Tracer = trace.get_tracer(__name__)


# async def astreamer(generator):
#     try:
#         for i in generator:
#             logger.info(i)
#             yield (i)
#             await asyncio.sleep(.1)
#     except asyncio.CancelledError:
#         print('cancelled')


@router.get("/health")
def healthcheck() -> Dict[str, str]:
    """Returns a health check"""
    with tracer.start_as_current_span("test") as span:
        span.set_attribute("test", "test")
    return {"status": "healthy"}


@router.post("/write-story", response_model=StoryResponse)
def write_story(model: StorytellerModel, topic: str):
    if model in [
        StorytellerModel.BEDROCK_CLAUDE_SONNET,
        StorytellerModel.BEDROCK_CLAUDE_HAIKU,
    ]:
        llm = ClaudeBedrockLlm(model.value)
    else:
        llm = OpenAILlm(model.value)

    logger.info(topic)

    data = llm.get_story(topic=topic)

    data = StoryResponse.model_validate(data)

    return data


@router.post("/write-story-async", response_model=StoryResponse)
async def write_story_async(model: StorytellerModel, topic: str):
    llm = ClaudeBedrockLlm(model.value)

    logger.info(topic)

    data = await llm.get_story_async(topic=topic)

    data = StoryResponse.model_validate(data)

    return data


@router.post("/stream-story")
def stream_story(model: StorytellerModel, topic: str):
    if model == StorytellerModel.BEDROCK_CLAUDE_SONNET:
        llm = ClaudeBedrockLlm(model.value)
    else:
        llm = OpenAILlm(model.value)

    logger.info(topic)

    return StreamingResponse(
        llm.stream_story(topic=topic), media_type="text/event-stream; charset=utf-8"
    )
