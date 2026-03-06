from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from src.config import settings
from src.database import TORTOISE_ORM
from src.orders.router import router as orders_router
from src.payments.router import router as payments_router


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    app.include_router(orders_router)
    app.include_router(payments_router)

    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=False,
        add_exception_handlers=True,
    )

    return app


app = create_app()
