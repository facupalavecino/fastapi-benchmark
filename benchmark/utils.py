import threading
import time
from typing import Tuple

from prometheus_client import (
    REGISTRY,
    CONTENT_TYPE_LATEST,
    generate_latest,
    Counter,
    Gauge,
    Histogram,
)
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp

INFO = Gauge(
    name="fastapi_app_info",
    documentation="FastAPI application information.",
    labelnames=["app_name"],
)
REQUESTS = Counter(
    name="fastapi_requests_total",
    documentation="Total count of requests by method and path.",
    labelnames=["method", "path", "app_name"],
)
RESPONSES = Counter(
    name="fastapi_responses_total",
    documentation="Total count of responses by method, path and status codes.",
    labelnames=["method", "path", "status_code", "app_name"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    name="fastapi_requests_duration_seconds",
    documentation="Histogram of requests processing time by path (in seconds)",
    labelnames=["method", "path", "app_name"],
)
EXCEPTIONS = Counter(
    name="fastapi_exceptions_total",
    documentation="Total count of exceptions raised by path and exception type",
    labelnames=["method", "path", "exception_type", "app_name"],
)
REQUESTS_IN_PROGRESS = Gauge(
    name="fastapi_requests_in_progress",
    documentation="Gauge of requests by method and path currently being processed",
    labelnames=["method", "path", "app_name"],
)

ACTIVE_THREADS = Gauge(
    name="fastapi_active_threads",
    documentation="Number of active threads in the FastAPI application.",
)
TIME_TO_FULL_RESPONSE = Histogram(
    name="time_to_full_response_seconds",
    documentation="Time to get the full response",
    labelnames=["provider", "model"]
)
TIME_TO_FIRST_BYTE = Histogram(
    name="time_to_first_byte_seconds",
    documentation="Time to first byte for the response",
    labelnames=["provider", "model"]
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, app_name: str) -> None:
        super().__init__(app)
        self.app_name = app_name
        INFO.labels(app_name=self.app_name).inc()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path, is_handled_path = self.get_path(request)

        if not is_handled_path:
            return await call_next(request)

        REQUESTS_IN_PROGRESS.labels(
            method=method, path=path, app_name=self.app_name
        ).inc()
        REQUESTS.labels(method=method, path=path, app_name=self.app_name).inc()
        before_time = time.perf_counter()
        try:
            response = await call_next(request)
        except BaseException as e:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            EXCEPTIONS.labels(
                method=method,
                path=path,
                exception_type=type(e).__name__,
                app_name=self.app_name,
            ).inc()
            raise e from None
        else:
            status_code = response.status_code
            after_time = time.perf_counter()

            REQUESTS_PROCESSING_TIME.labels(
                method=method, path=path, app_name=self.app_name
            ).observe(after_time - before_time)
        finally:
            RESPONSES.labels(
                method=method,
                path=path,
                status_code=status_code,
                app_name=self.app_name,
            ).inc()
            REQUESTS_IN_PROGRESS.labels(
                method=method, path=path, app_name=self.app_name
            ).dec()

        return response

    @staticmethod
    def get_path(request: Request) -> Tuple[str, bool]:
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return route.path, True

        return request.url.path, False


def metrics(request: Request) -> Response:
    ACTIVE_THREADS.set(threading.active_count())
    return Response(
        generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST}
    )
