from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AcquiringStartRequest(BaseModel):
    order_id: int
    amount: Decimal


class AcquiringStartResponse(BaseModel):
    bank_payment_id: str


class AcquiringCheckRequest(BaseModel):
    bank_payment_id: str


class AcquiringCheckResponse(BaseModel):
    bank_payment_id: str
    amount: Decimal
    status: str
    paid_at: datetime | None = None


class ErrorResponse(BaseModel):
    error: str
