from enum import StrEnum


class PaymentStatus(StrEnum):
    NOT_PAID = "not_paid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
