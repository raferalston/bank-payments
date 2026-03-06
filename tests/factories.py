import random
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from faker import Faker

from src.orders.constants import PaymentStatus
from src.orders.models import Order
from src.payments.constants import PaymentOperationStatus, PaymentType
from src.payments.models import Payment

fake = Faker()


async def create_order(
    amount: Decimal | None = None,
    payment_status: PaymentStatus = PaymentStatus.NOT_PAID,
) -> Order:
    if amount is None:
        amount = Decimal(str(round(random.uniform(100, 50000), 2)))
    return await Order.create(amount=amount, payment_status=payment_status)


async def create_payment(
    order: Order,
    amount: Decimal | None = None,
    payment_type: PaymentType = PaymentType.CASH,
    operation_status: PaymentOperationStatus = PaymentOperationStatus.DEPOSITED,
    bank_payment_id: str | None = None,
    paid_at: datetime | None = None,
) -> Payment:
    if amount is None:
        amount = Decimal(str(round(random.uniform(10, float(order.amount)), 2)))
    if payment_type == PaymentType.ACQUIRING and bank_payment_id is None:
        bank_payment_id = str(uuid4())
    if operation_status == PaymentOperationStatus.DEPOSITED and paid_at is None:
        paid_at = fake.date_time_between(start_date="-30d", end_date="now", tzinfo=UTC)
    return await Payment.create(
        order=order,
        amount=amount,
        payment_type=payment_type,
        operation_status=operation_status,
        bank_payment_id=bank_payment_id,
        paid_at=paid_at,
    )


async def create_order_with_payments(
    amount: Decimal = Decimal("1000.00"),
    payment_status: PaymentStatus = PaymentStatus.NOT_PAID,
    payments_count: int = 0,
    payment_type: PaymentType = PaymentType.CASH,
    payment_operation_status: PaymentOperationStatus = PaymentOperationStatus.DEPOSITED,
) -> tuple[Order, list[Payment]]:
    order = await create_order(amount=amount, payment_status=payment_status)
    payments = []
    for _ in range(payments_count):
        payment_amount = Decimal(str(round(float(amount) / max(payments_count, 1), 2)))
        p = await create_payment(
            order=order,
            amount=payment_amount,
            payment_type=payment_type,
            operation_status=payment_operation_status,
        )
        payments.append(p)
    return order, payments
