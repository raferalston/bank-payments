from pydantic_settings import BaseSettings


class BankConfig(BaseSettings):
    BANK_API_URL: str = "http://localhost:8001"
    BANK_REQUEST_TIMEOUT: float = 10.0
    BANK_MAX_RETRIES: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


bank_settings = BankConfig()
