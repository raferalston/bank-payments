from urllib.parse import urlparse

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

from src.config import settings
from src.database import TORTOISE_ORM
from src.main import app

TEST_DB_URL = str(settings.test_database_url)

TEST_TORTOISE_ORM = {
    **TORTOISE_ORM,
    "connections": {"default": TEST_DB_URL},
}


async def _ensure_test_db_exists() -> None:
    """Создать тестовую БД, если она ещё не существует."""
    parsed = urlparse(TEST_DB_URL)
    db_name = parsed.path.lstrip("/")
    admin_url = TEST_DB_URL.rsplit("/", 1)[0] + "/postgres"
    conn = await asyncpg.connect(admin_url)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


@pytest.fixture(autouse=True)
async def db():
    """Инициализация Tortoise и очистка таблиц перед каждым тестом (используется тестовая БД)."""
    await _ensure_test_db_exists()
    await Tortoise.init(config=TEST_TORTOISE_ORM)
    await Tortoise.generate_schemas()
    conn = Tortoise.get_connection("default")
    await conn.execute_query('TRUNCATE TABLE payment, "order" RESTART IDENTITY CASCADE')
    try:
        yield
    finally:
        await Tortoise.close_connections()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def orders_dataset():
    """Заказы из сида, созданные в БД."""
    from src.orders.seed import create_orders_from_dataset

    return await create_orders_from_dataset()
