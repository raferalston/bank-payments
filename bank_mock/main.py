from fastapi import FastAPI

from bank_mock.router import router

app = FastAPI(
    title="Bank Mock API",
    version="0.1.0",
    description="Mock-сервис банковского API для тестирования эквайринга",
)

app.include_router(router)
