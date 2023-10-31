import logging
import logging.config
from importlib.metadata import version
from contextlib import asynccontextmanager

from fastapi import FastAPI
from benchmark.utils import PrometheusMiddleware, metrics

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


app = FastAPI(title=PROJECT_NAME, lifespan=lifespan, version=app_version)

app.add_middleware(PrometheusMiddleware, app_name="fastapi-service-sync")

app.add_route("/metrics", metrics)

app.include_router(router)
