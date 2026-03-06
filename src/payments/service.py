from datetime import UTC, datetime
from decimal import Decimal

from tortoise.expressions import Q
from tortoise.functions import Coalesce, Sum
from tortoise.transactions import in_transaction

from src.bank.client import bank_client
from src.bank.constants import BankPaymentStatus
from src.bank.exceptions import BankPaymentNotFoundError
from src.orders import service as order_service
from src.orders.constants import PaymentStatus
from src.orders.models import Order
from src.payments.constants import PaymentOperationStatus, PaymentType
from src.payments.exceptions import (
    OrderAlreadyPaidError,
    PaymentAlreadyRefundedError,
    PaymentAmountExceededError,
    PaymentNotDepositedError,
    UnsupportedPaymentTypeError,
)
from src.payments.models import Payment


async def get_payments_by_order(order_id: int) -> list[Payment]:
    return await Payment.filter(order_id=order_id).order_by("-created_at")


async def get_remaining_balance(order: Order) -> Decimal:
    """Подсчитать оставшуюся к оплате сумму заказа."""
    order_with_paid = (
        await Order.get(id=order.id)
        .annotate(
            paid_total=Coalesce(
                Sum("payments__amount", _filter=Q(payments__operation_status=PaymentOperationStatus.DEPOSITED)),
                Decimal("0"),
            )
        )
        .only("paid_total")
    )
    return order.amount - order_with_paid.paid_total


async def _validate_deposit(order: Order, amount: Decimal) -> Order:
    """Общая валидация перед созданием платежа (внутри транзакции)."""
    order = await Order.get(id=order.id).select_for_update()

    if order.payment_status == PaymentStatus.PAID:
        raise OrderAlreadyPaidError()

    remaining = await get_remaining_balance(order)
    if amount > remaining:
        raise PaymentAmountExceededError()
    return order


async def _create_cash_deposit(order: Order, amount: Decimal) -> Payment:
    """Наличная оплата — платёж сразу подтверждён."""
    async with in_transaction():
        order = await _validate_deposit(order, amount)

        payment = await Payment.create(
            order=order,
            amount=amount,
            payment_type=PaymentType.CASH,
            operation_status=PaymentOperationStatus.DEPOSITED,
            paid_at=datetime.now(UTC),
        )

        await order_service.recalculate_payment_status(order)
    return payment


async def _create_acquiring_deposit(order: Order, amount: Decimal) -> Payment:
    """Банковский эквайринг — создаём PENDING-платёж и инициируем оплату в банке."""
    async with in_transaction():
        order = await _validate_deposit(order, amount)

        bank_response = await bank_client.acquiring_start(
            order_id=order.id,
            amount=amount,
        )

        payment = await Payment.create(
            order=order,
            amount=amount,
            payment_type=PaymentType.ACQUIRING,
            operation_status=PaymentOperationStatus.PENDING,
            bank_payment_id=bank_response.bank_payment_id,
        )

    # Избегаем циклической зависимости между сервисами
    from src.payments.tasks import confirm_acquiring_payment_task

    confirm_acquiring_payment_task.delay(payment.id)

    return payment


_DEPOSIT_HANDLERS = {
    PaymentType.CASH: _create_cash_deposit,
    PaymentType.ACQUIRING: _create_acquiring_deposit,
}


async def create_deposit(order: Order, amount: Decimal, payment_type: PaymentType) -> Payment:
    """Создать платёж по заказу. Логика зависит от типа оплаты."""
    handler = _DEPOSIT_HANDLERS.get(payment_type)
    if handler is None:
        raise UnsupportedPaymentTypeError(str(payment_type))
    return await handler(order, amount)


async def confirm_acquiring_payment(payment: Payment) -> Payment:
    """Подтвердить банковский платёж по результату acquiring_check.
    Симулируем ожидание результата оплаты в банке."""
    try:
        check = await bank_client.acquiring_check(payment.bank_payment_id)
    except BankPaymentNotFoundError:
        payment.operation_status = PaymentOperationStatus.FAILED
        await payment.save()
        return payment

    # Обработка неуспешной оплаты
    if check.status == BankPaymentStatus.FAILED:
        payment.operation_status = PaymentOperationStatus.FAILED
        await payment.save()
        return payment

    # Обработка успешной оплаты
    if check.status == BankPaymentStatus.COMPLETED:
        async with in_transaction():
            payment = await Payment.get(id=payment.id).select_for_update()
            payment.operation_status = PaymentOperationStatus.DEPOSITED
            payment.paid_at = check.paid_at or datetime.now(UTC)
            await payment.save()

            order = await Order.get(id=payment.order_id)
            await order_service.recalculate_payment_status(order)
    return payment


async def refund_payment(payment: Payment) -> Payment:
    """Выполнить возврат по существующему платежу."""
    async with in_transaction():
        payment = await Payment.get(id=payment.id).select_for_update()
        if payment.operation_status == PaymentOperationStatus.REFUNDED:
            raise PaymentAlreadyRefundedError()

        if payment.operation_status != PaymentOperationStatus.DEPOSITED:
            raise PaymentNotDepositedError()

        payment.operation_status = PaymentOperationStatus.REFUNDED
        payment.updated_at = datetime.now(UTC)
        await payment.save()

        order = await Order.get(id=payment.order_id)
        await order_service.recalculate_payment_status(order)
    return payment
