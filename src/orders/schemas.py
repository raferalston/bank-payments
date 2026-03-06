from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from src.orders.constants import PaymentStatus


class OrderResponse(BaseModel):
    id: int
    amount: Decimal = Field(decimal_places=2)
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
