from src.payments.exceptions import PaymentNotFoundError
from src.payments.models import Payment


async def valid_payment_id(payment_id: int) -> Payment:
    payment = await Payment.get_or_none(id=payment_id).select_related("order")
    if not payment:
        raise PaymentNotFoundError()
    return payment
