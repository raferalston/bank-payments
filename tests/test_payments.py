from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from src.bank.constants import BankPaymentStatus
from src.bank.exceptions import BankPaymentNotFoundError
from src.bank.schemas import AcquiringCheckResponse, AcquiringStartResponse
from src.orders.constants import PaymentStatus
from src.orders.models import Order
from src.payments import service
from src.payments.constants import PaymentOperationStatus, PaymentType
from src.payments.exceptions import (
    OrderAlreadyPaidError,
    PaymentAlreadyRefundedError,
    PaymentAmountExceededError,
    PaymentNotDepositedError,
)
from tests.factories import create_order, create_payment


async def test_get_payments_by_order_returns_payments():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("300.00"))
    await create_payment(order=order, amount=Decimal("200.00"))
    payments = await service.get_payments_by_order(order.id)
    assert len(payments) == 2
    assert payments[0].created_at >= payments[1].created_at


async def test_get_payments_by_order_empty():
    order = await create_order()
    payments = await service.get_payments_by_order(order.id)
    assert payments == []


async def test_get_payments_by_order_does_not_mix_orders():
    order1 = await create_order(amount=Decimal("1000.00"))
    order2 = await create_order(amount=Decimal("2000.00"))
    await create_payment(order=order1, amount=Decimal("100.00"))
    await create_payment(order=order2, amount=Decimal("200.00"))
    payments = await service.get_payments_by_order(order1.id)
    assert len(payments) == 1
    assert payments[0].order_id == order1.id


async def test_remaining_balance_no_payments():
    order = await create_order(amount=Decimal("1000.00"))
    remaining = await service.get_remaining_balance(order)
    assert remaining == Decimal("1000.00")


async def test_remaining_balance_with_deposited():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("300.00"))
    remaining = await service.get_remaining_balance(order)
    assert remaining == Decimal("700.00")


async def test_remaining_balance_ignores_refunded():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(
        order=order,
        amount=Decimal("500.00"),
        operation_status=PaymentOperationStatus.REFUNDED,
    )
    remaining = await service.get_remaining_balance(order)
    assert remaining == Decimal("1000.00")


async def test_remaining_balance_fully_paid():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("1000.00"))
    remaining = await service.get_remaining_balance(order)
    assert remaining == Decimal("0.00")


async def test_create_cash_deposit():
    order = await create_order(amount=Decimal("1000.00"))
    payment = await service.create_deposit(order, Decimal("500.00"), PaymentType.CASH)
    assert payment.amount == Decimal("500.00")
    assert payment.payment_type == PaymentType.CASH
    assert payment.operation_status == PaymentOperationStatus.DEPOSITED
    assert payment.paid_at is not None


async def test_create_cash_deposit_updates_order_status():
    order = await create_order(amount=Decimal("1000.00"))
    await service.create_deposit(order, Decimal("1000.00"), PaymentType.CASH)
    refreshed = await Order.get(id=order.id)
    assert refreshed.payment_status == PaymentStatus.PAID


async def test_create_cash_deposit_partial_updates_status():
    order = await create_order(amount=Decimal("1000.00"))
    await service.create_deposit(order, Decimal("500.00"), PaymentType.CASH)
    refreshed = await Order.get(id=order.id)
    assert refreshed.payment_status == PaymentStatus.PARTIALLY_PAID


async def test_create_deposit_raises_when_order_already_paid():
    order = await create_order(amount=Decimal("100.00"), payment_status=PaymentStatus.PAID)
    await create_payment(order=order, amount=Decimal("100.00"))
    with pytest.raises(OrderAlreadyPaidError):
        await service.create_deposit(order, Decimal("50.00"), PaymentType.CASH)


async def test_create_deposit_raises_when_amount_exceeds_remaining():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("800.00"))
    with pytest.raises(PaymentAmountExceededError):
        await service.create_deposit(order, Decimal("300.00"), PaymentType.CASH)


@patch("src.payments.service.bank_client")
@patch("src.payments.tasks.confirm_acquiring_payment_task")
async def test_create_acquiring_deposit(mock_task, mock_bank):
    mock_bank.acquiring_start = AsyncMock(return_value=AcquiringStartResponse(bank_payment_id="bank-123"))
    order = await create_order(amount=Decimal("1000.00"))
    payment = await service.create_deposit(order, Decimal("500.00"), PaymentType.ACQUIRING)
    assert payment.payment_type == PaymentType.ACQUIRING
    assert payment.operation_status == PaymentOperationStatus.PENDING
    assert payment.bank_payment_id == "bank-123"
    mock_bank.acquiring_start.assert_called_once_with(order_id=order.id, amount=Decimal("500.00"))
    mock_task.delay.assert_called_once_with(payment.id)


@patch("src.payments.service.bank_client")
async def test_confirm_acquiring_payment_success(mock_bank):
    paid_at = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
    mock_bank.acquiring_check = AsyncMock(
        return_value=AcquiringCheckResponse(
            bank_payment_id="bank-123",
            amount=Decimal("500.00"),
            status=BankPaymentStatus.COMPLETED,
            paid_at=paid_at,
        )
    )
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(
        order=order,
        amount=Decimal("500.00"),
        payment_type=PaymentType.ACQUIRING,
        operation_status=PaymentOperationStatus.PENDING,
        bank_payment_id="bank-123",
    )
    result = await service.confirm_acquiring_payment(payment)
    assert result.operation_status == PaymentOperationStatus.DEPOSITED
    assert result.paid_at == paid_at
    refreshed_order = await Order.get(id=order.id)
    assert refreshed_order.payment_status == PaymentStatus.PARTIALLY_PAID


@patch("src.payments.service.bank_client")
async def test_confirm_acquiring_payment_failed(mock_bank):
    mock_bank.acquiring_check = AsyncMock(
        return_value=AcquiringCheckResponse(
            bank_payment_id="bank-456",
            amount=Decimal("500.00"),
            status=BankPaymentStatus.FAILED,
        )
    )
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(
        order=order,
        amount=Decimal("500.00"),
        payment_type=PaymentType.ACQUIRING,
        operation_status=PaymentOperationStatus.PENDING,
        bank_payment_id="bank-456",
    )
    result = await service.confirm_acquiring_payment(payment)
    assert result.operation_status == PaymentOperationStatus.FAILED


@patch("src.payments.service.bank_client")
async def test_confirm_acquiring_payment_not_found_in_bank(mock_bank):
    mock_bank.acquiring_check = AsyncMock(side_effect=BankPaymentNotFoundError())
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(
        order=order,
        amount=Decimal("500.00"),
        payment_type=PaymentType.ACQUIRING,
        operation_status=PaymentOperationStatus.PENDING,
        bank_payment_id="bank-gone",
    )
    result = await service.confirm_acquiring_payment(payment)
    assert result.operation_status == PaymentOperationStatus.FAILED


async def test_refund_deposited_payment():
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(order=order, amount=Decimal("500.00"))
    result = await service.refund_payment(payment)
    assert result.operation_status == PaymentOperationStatus.REFUNDED


async def test_refund_updates_order_status():
    order = await create_order(amount=Decimal("1000.00"), payment_status=PaymentStatus.PAID)
    payment = await create_payment(order=order, amount=Decimal("1000.00"))
    await service.refund_payment(payment)
    refreshed = await Order.get(id=order.id)
    assert refreshed.payment_status == PaymentStatus.NOT_PAID


async def test_refund_already_refunded_raises():
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(
        order=order,
        amount=Decimal("500.00"),
        operation_status=PaymentOperationStatus.REFUNDED,
    )
    with pytest.raises(PaymentAlreadyRefundedError):
        await service.refund_payment(payment)


async def test_refund_pending_raises():
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(
        order=order,
        amount=Decimal("500.00"),
        payment_type=PaymentType.ACQUIRING,
        operation_status=PaymentOperationStatus.PENDING,
    )
    with pytest.raises(PaymentNotDepositedError):
        await service.refund_payment(payment)


async def test_api_create_cash_payment(client):
    order = await create_order(amount=Decimal("1000.00"))
    response = await client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "500.00",
            "payment_type": "cash",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order.id
    assert Decimal(data["amount"]) == Decimal("500.00")
    assert data["payment_type"] == "cash"
    assert data["operation_status"] == "deposited"
    assert data["paid_at"] is not None


async def test_api_create_payment_nonexistent_order(client):
    response = await client.post(
        "/payments",
        json={
            "order_id": 99999,
            "amount": "100.00",
            "payment_type": "cash",
        },
    )
    assert response.status_code == 404


async def test_api_create_payment_exceeds_balance(client):
    order = await create_order(amount=Decimal("100.00"))
    response = await client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "200.00",
            "payment_type": "cash",
        },
    )
    assert response.status_code == 400


async def test_api_create_payment_invalid_amount(client):
    order = await create_order(amount=Decimal("1000.00"))
    response = await client.post(
        "/payments",
        json={
            "order_id": order.id,
            "amount": "-10.00",
            "payment_type": "cash",
        },
    )
    assert response.status_code == 422


async def test_api_get_order_payments(client):
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("300.00"))
    await create_payment(order=order, amount=Decimal("200.00"))
    response = await client.get(f"/payments/by-order/{order.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_api_get_order_payments_empty(client):
    order = await create_order()
    response = await client.get(f"/payments/by-order/{order.id}")
    assert response.status_code == 200
    assert response.json() == []


async def test_api_get_order_payments_nonexistent_order(client):
    response = await client.get("/payments/by-order/99999")
    assert response.status_code == 404


async def test_api_refund_payment(client):
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(order=order, amount=Decimal("500.00"))
    response = await client.post(f"/payments/{payment.id}/refund")
    assert response.status_code == 200
    assert response.json()["operation_status"] == "refunded"


async def test_api_refund_nonexistent_payment(client):
    response = await client.post("/payments/99999/refund")
    assert response.status_code == 404


async def test_api_refund_already_refunded(client):
    order = await create_order(amount=Decimal("1000.00"))
    payment = await create_payment(
        order=order,
        amount=Decimal("500.00"),
        operation_status=PaymentOperationStatus.REFUNDED,
    )
    response = await client.post(f"/payments/{payment.id}/refund")
    assert response.status_code == 400


async def test_api_remaining_balance(client):
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("300.00"))
    response = await client.get(f"/payments/remaining-balance/{order.id}")
    assert response.status_code == 200
    assert Decimal(response.json()["amount"]) == Decimal("700.00")


async def test_api_remaining_balance_no_payments(client):
    order = await create_order(amount=Decimal("1000.00"))
    response = await client.get(f"/payments/remaining-balance/{order.id}")
    assert response.status_code == 200
    assert Decimal(response.json()["amount"]) == Decimal("1000.00")


async def test_api_remaining_balance_nonexistent_order(client):
    response = await client.get("/payments/remaining-balance/99999")
    assert response.status_code == 404
