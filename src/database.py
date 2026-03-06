from src.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": str(settings.DATABASE_URL),
    },
    "apps": {
        "models": {
            "models": [
                "src.orders.models",
                "src.payments.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
