import asyncio
import boto3
from botocore.client import ClientError
import logging
import random
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from opentelemetry import trace

from benchmark.api.schemas import StoryResponse
from benchmark.core import constants
from benchmark.core.config import settings
from benchmark.llms.bedrock import ClaudeBedrockLlm


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()

tracer: trace.Tracer = trace.get_tracer(__name__)


@router.get("/health")
def healthcheck() -> Dict[str, str]:
    """Returns a health check"""
    with tracer.start_as_current_span("test") as span:
        span.set_attribute("test", "test")
    return {"status": "healthy"}


@router.get("/sync-endpoint")
def sync_req() -> Dict[str, str]:
    """Sleeps for 1 second and returns a response"""
    time.sleep(random.randint(1, 3))
    return {"status": "Slept synchronously"}

@router.get("/async-endpoint")
async def async_endpoint() -> Dict[str, str]:
    await asyncio.sleep(random.randint(1, 3))
    return {"message": "Slept asynchronously"}


@router.get("/sync-s3")
def sync_s3_req(request: Request) -> Dict[str, str]:
    """Sleeps for 1 second and returns a response"""

    s3_client: boto3.client = request.app.state.s3_client

    try:
        logger.info(f"About to fetch {settings.AWS_S3_BUCKET_NAME}/{constants.S3_DATA_KEY}")
        response = s3_client.get_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=constants.S3_DATA_KEY)
    except ClientError as e:
        logger.exception(e)
    except Exception as e:
        logger.exception(e)
        raise Exception from e
    return {"ETag": response["ETag"]}


# @router.get("/async-s3")
# async def async_s3_req(request: Request):
#     """Fetches the file from S3 asynchronously."""
#     session: aioboto3.Session = request.app.state.aioboto3_session

#     try:
#         async with session.client("s3", endpoint_url=settings.AWS_S3_ENDPOINT_URL) as s3_client:

#             s3_object = await s3_client.get_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=constants.S3_DATA_KEY)
    
#     except ClientError as e:
#         logger.exception(e)
#         raise HTTPException(status_code=500, detail=str(e))
    
#     except Exception as e:
#         logger.exception(e)
#         raise HTTPException(status_code=500, detail=str(e))

#     return {"ETag": s3_object["ETag"]}


@router.post("/write-story", response_model=StoryResponse)
def bedrock_write_story(topic: str):

    try:
        model = ClaudeBedrockLlm()

    except Exception as e:
        logger.exception(e)

    logger.info(topic)

    data = model.get_story(topic=topic)

    data = StoryResponse.model_validate(data)

    return data


async def astreamer(generator):
    try:
        for i in generator:
            logger.info(i)
            yield (i)
            await asyncio.sleep(.1)
    except asyncio.CancelledError:        
        print('cancelled')

@router.post("/stream-story")
def bedrock_stream_story(topic: str):

    try:
        model = ClaudeBedrockLlm()

    except Exception as e:
        logger.exception(e)

    logger.info(topic)

    return StreamingResponse(model.stream_story(topic=topic), media_type="text/event-stream; charset=utf-8")
