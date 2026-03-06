from fastapi import APIRouter, Depends, status

from src.orders.dependencies import valid_order_id
from src.orders.models import Order
from src.payments import service
from src.payments.dependencies import valid_payment_id
from src.payments.models import Payment
from src.payments.schemas import BalanceResponse, PaymentCreate, PaymentResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(data: PaymentCreate):
    """Создание платежа в зависимости от типа оплаты.
    service.create_deposit - Определяет тип оплаты и создает платеж."""
    order = await valid_order_id(data.order_id)
    payment = await service.create_deposit(
        order=order,
        amount=data.amount,
        payment_type=data.payment_type,
    )
    return PaymentResponse.model_validate(payment, from_attributes=True)


@router.get("/by-order/{order_id}", response_model=list[PaymentResponse])
async def get_order_payments(order: Order = Depends(valid_order_id)):
    payments = await service.get_payments_by_order(order.id)
    return [PaymentResponse.model_validate(p, from_attributes=True) for p in payments]


@router.post("/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(payment: Payment = Depends(valid_payment_id)):
    refunded = await service.refund_payment(payment)
    return PaymentResponse.model_validate(refunded, from_attributes=True)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(payment: Payment = Depends(valid_payment_id)):
    confirmed = await service.confirm_acquiring_payment(payment)
    return PaymentResponse.model_validate(confirmed, from_attributes=True)


@router.get("/remaining-balance/{order_id}", response_model=BalanceResponse)
async def get_remaining_balance(order: Order = Depends(valid_order_id)):
    remaining_amount = await service.get_remaining_balance(order)
    return BalanceResponse(amount=remaining_amount)
