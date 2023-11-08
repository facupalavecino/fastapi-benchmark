from typing import List, Optional

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_DEFAULT_REGION: str
    AWS_S3_ENDPOINT_URL: Optional[str] = None
    AWS_S3_BUCKET_NAME: str

    class Config:
        case_sensitive = True


settings = Settings()
