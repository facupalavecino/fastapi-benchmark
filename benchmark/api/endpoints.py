import asyncio
import logging
import random
import time
from typing import Dict

from fastapi import APIRouter
from opentelemetry import trace


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
