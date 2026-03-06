from datetime import datetime
from decimal import Decimal
from uuid import uuid4

payments: dict[str, dict] = {}


def create_payment(order_id: int, amount: Decimal) -> str:
    bank_payment_id = str(uuid4())
    payments[bank_payment_id] = {
        "bank_payment_id": bank_payment_id,
        "order_id": order_id,
        "amount": amount,
        "status": "completed",
        "paid_at": datetime.now().isoformat(),
    }
    return bank_payment_id


def get_payment(bank_payment_id: str) -> dict | None:
    return payments.get(bank_payment_id)
