from decimal import Decimal

from tortoise.expressions import Q
from tortoise.functions import Coalesce, Sum

from src.orders.constants import PaymentStatus
from src.orders.models import Order
from src.payments.constants import PaymentOperationStatus


async def get_orders() -> list[Order]:
    return await Order.all().order_by("-created_at")


async def get_order_with_payments(order_id: int) -> Order:
    return await Order.get(id=order_id).prefetch_related("payments")


async def recalculate_payment_status(order: Order) -> Order:
    """Пересчитать статус оплаты заказа на основе связанных платежей."""
    await order.fetch_related("payments")

    order_with_paid_total = await Order.get(id=order.id).annotate(
        paid_total=Coalesce(
            Sum("payments__amount", _filter=Q(payments__operation_status=PaymentOperationStatus.DEPOSITED)),
            Decimal("0"),
        )
    )

    if order_with_paid_total.paid_total >= order.amount:
        order.payment_status = PaymentStatus.PAID
    elif order_with_paid_total.paid_total > Decimal("0"):
        order.payment_status = PaymentStatus.PARTIALLY_PAID
    else:
        order.payment_status = PaymentStatus.NOT_PAID

    await order.save()
    return order
