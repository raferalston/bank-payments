from decimal import Decimal

from src.orders.constants import PaymentStatus
from src.orders.models import Order

ORDER_DATASET = [
    {"amount": Decimal("1000.00"), "payment_status": PaymentStatus.NOT_PAID},
    {"amount": Decimal("2500.50"), "payment_status": PaymentStatus.NOT_PAID},
    {"amount": Decimal("750.00"), "payment_status": PaymentStatus.PARTIALLY_PAID},
    {"amount": Decimal("5000.00"), "payment_status": PaymentStatus.PARTIALLY_PAID},
    {"amount": Decimal("320.00"), "payment_status": PaymentStatus.PAID},
    {"amount": Decimal("15000.00"), "payment_status": PaymentStatus.PAID},
]


async def create_orders_from_dataset(dataset: list[dict] | None = None) -> list[Order]:
    created: list[Order] = []
    for item in dataset or ORDER_DATASET:
        order = await Order.create(
            amount=item["amount"],
            payment_status=item["payment_status"],
        )
        created.append(order)
    return created


def get_order_dataset() -> list[dict]:
    return list(ORDER_DATASET)
