import aioboto3
import boto3
import logging
import logging.config

from importlib.metadata import version
from contextlib import asynccontextmanager

from fastapi import FastAPI

from benchmark.api.endpoints import router
from benchmark.core.config import settings
from benchmark.core.constants import PROJECT_NAME
from benchmark.core.logging.dict_config import LOGGING_CONFIG
from benchmark.utils import PrometheusMiddleware, metrics

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

    logger.info(f"Connecting to S3 bucket: {settings.AWS_S3_BUCKET_NAME}")

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    )

    try:
        aioboto3_session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    except Exception as e:
        logger.exception(e)

    app.state.s3_client = s3_client
    app.state.aioboto3_session = aioboto3_session

    logger.info("Done! App ready to accept requests...")

    yield

    logger.info("Shutting down application...")


app = FastAPI(title=PROJECT_NAME, lifespan=lifespan, version=app_version)

app.add_middleware(PrometheusMiddleware, app_name="fastapi-service-sync")

app.add_route("/metrics", metrics)

app.include_router(router)
