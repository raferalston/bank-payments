from src.orders.exceptions import OrderNotFoundError
from src.orders.models import Order


async def valid_order_id(order_id: int) -> Order:
    order = await Order.get_or_none(id=order_id)
    if not order:
        raise OrderNotFoundError()
    return order
