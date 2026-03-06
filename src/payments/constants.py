from enum import StrEnum


class PaymentType(StrEnum):
    CASH = "cash"
    ACQUIRING = "acquiring"


class PaymentOperationStatus(StrEnum):
    PENDING = "pending"
    DEPOSITED = "deposited"
    REFUNDED = "refunded"
    FAILED = "failed"
