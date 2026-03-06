from urllib.parse import urlparse, urlunparse

from pydantic import ConfigDict, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "IT Guru Payment Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: PostgresDsn = "postgres://it-guru:it-guru@localhost:5432/it-guru"
    TEST_DATABASE_URL: PostgresDsn | None = None  # БД для тестов; если не задана — используется {DATABASE_URL}_test

    REDIS_URL: str = "redis://localhost:6379/0"

    BANK_API_URL: str = "http://localhost:8001"

    BANK_REQUEST_TIMEOUT: float = 10.0

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def celery_broker_url(self) -> str:
        return str(self.REDIS_URL)

    @property
    def test_database_url(self) -> PostgresDsn:
        """URL тестовой БД: TEST_DATABASE_URL или основная БД с суффиксом _test."""
        if self.TEST_DATABASE_URL is not None:
            return self.TEST_DATABASE_URL
        parsed = urlparse(str(self.DATABASE_URL))
        path = parsed.path.rstrip("/")
        new_path = f"{path}_test"
        return PostgresDsn(urlunparse(parsed._replace(path=new_path)))


settings = Settings()
