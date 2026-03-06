import asyncio
import logging

from tortoise import Tortoise

from src.celery_app import app
from src.database import TORTOISE_ORM
from src.payments.constants import PaymentOperationStatus

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
RETRY_COUNTDOWN_SECONDS = 5


async def _init_tortoise() -> None:
    if Tortoise._inited:
        return
    await Tortoise.init(config=TORTOISE_ORM)


async def _confirm_payment_once(payment_id: int) -> str:
    """Одна попытка подтверждения эквайринг-платежа. Возвращает operation_status после попытки."""
    await _init_tortoise()

    from src.payments.models import Payment
    from src.payments.service import confirm_acquiring_payment

    payment = await Payment.get_or_none(id=payment_id)
    if not payment:
        return "not_found"
    if payment.operation_status != PaymentOperationStatus.PENDING:
        return payment.operation_status.value

    payment = await confirm_acquiring_payment(payment)
    return payment.operation_status.value


async def _mark_payment_failed(payment_id: int) -> None:
    """Пометить платёж как FAILED после исчерпания попыток."""
    await _init_tortoise()

    from src.payments.models import Payment

    payment = await Payment.get_or_none(id=payment_id)
    if payment and payment.operation_status == PaymentOperationStatus.PENDING:
        payment.operation_status = PaymentOperationStatus.FAILED
        await payment.save()


@app.task(bind=True)
def confirm_acquiring_payment_task(self, payment_id: int, attempt: int = 1) -> None:
    """Отложенная задача: до 5 попыток подтвердить платёж с интервалом 5 секунд.
    Между попытками воркер освобождается (следующая попытка планируется через countdown)."""
    logger.info("Payment %s: attempt %s/%s", payment_id, attempt, MAX_ATTEMPTS)

    try:
        status = asyncio.run(_confirm_payment_once(payment_id))
    except Exception:
        logger.exception("Payment %s: attempt %s failed with error", payment_id, attempt)
        status = PaymentOperationStatus.PENDING.value

    if status != PaymentOperationStatus.PENDING.value:
        logger.info("Payment %s: finished with status '%s' on attempt %s", payment_id, status, attempt)
        return

    if attempt >= MAX_ATTEMPTS:
        logger.warning("Payment %s: exhausted %s attempts, marking as FAILED", payment_id, MAX_ATTEMPTS)
        asyncio.run(_mark_payment_failed(payment_id))
        return

    self.apply_async(args=[payment_id], kwargs={"attempt": attempt + 1}, countdown=RETRY_COUNTDOWN_SECONDS)
