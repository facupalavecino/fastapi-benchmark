import logging
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
