import logging
import logging.config
from importlib.metadata import version
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app, Counter, Histogram

from benchmark.api.endpoints import router
from benchmark.core.constants import PROJECT_NAME
from benchmark.core.logging.dict_config import LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("benchmark")

app_version = version("fastapi-async-benchmark")


@asynccontextmanager
async def lifespan(app: FastAPI):  # pylint: disable=redefined-outer-name
    """Lifespan handler that let us execute code before
    the application starts, and during application shutdown.

    Parameters
    ----------
    app : FastAPI
        The application instance

    Notes
    -----
    More about lifespan events: [Lifespan](https://www.starlette.io/lifespan/)
    """
    logger.info(f"Initializing API v{app_version}")

    logger.info("Done! App ready to accept requests...")

    yield

    logger.info("Shutting down application...")


REQUEST_COUNT = Counter(
    "request_count", "Number of requests received", ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds", "Request latency", ["endpoint"]
)

app = FastAPI(title=PROJECT_NAME, lifespan=lifespan, version=app_version)

@app.middleware("http")
async def collect_metrics(request, call_next):
    path = request.url.path
    method = request.method
    endpoint = f"{method} {path}"
    
    with REQUEST_LATENCY.labels(endpoint).time():
        response = await call_next(request)
    
    REQUEST_COUNT.labels(method, path, response.status_code).inc()
    
    return response

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(router)
