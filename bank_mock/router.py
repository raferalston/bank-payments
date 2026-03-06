from fastapi import APIRouter, HTTPException, Query

from bank_mock import storage
from bank_mock.schemas import (
    AcquiringCheckResponse,
    AcquiringStartRequest,
    AcquiringStartResponse,
)

router = APIRouter()


@router.post("/acquiring_start", response_model=AcquiringStartResponse)
async def acquiring_start(data: AcquiringStartRequest):
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    bank_payment_id = storage.create_payment(order_id=data.order_id, amount=data.amount)
    return AcquiringStartResponse(bank_payment_id=bank_payment_id)


@router.get("/acquiring_check", response_model=AcquiringCheckResponse)
async def acquiring_check(bank_payment_id: str = Query(...)):
    payment = storage.get_payment(bank_payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return AcquiringCheckResponse(**payment)
