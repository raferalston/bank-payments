from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.payments.constants import PaymentOperationStatus, PaymentType


class PaymentCreate(BaseModel):
    order_id: int
    amount: Decimal = Field(gt=0, decimal_places=2)
    payment_type: PaymentType


class PaymentRefund(BaseModel):
    reason: str | None = None


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: Decimal = Field(decimal_places=2)
    payment_type: PaymentType
    operation_status: PaymentOperationStatus
    bank_payment_id: str | None = None
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BalanceResponse(BaseModel):
    amount: Decimal = Field(decimal_places=2)
