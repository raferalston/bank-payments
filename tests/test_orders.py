from decimal import Decimal

from src.orders import service
from src.orders.constants import PaymentStatus
from src.orders.models import Order
from src.orders.seed import ORDER_DATASET
from src.payments.constants import PaymentOperationStatus, PaymentType
from tests.factories import create_order, create_payment


async def test_get_orders_returns_all(orders_dataset):
    orders = await service.get_orders()
    assert len(orders) == len(ORDER_DATASET)


async def test_get_orders_ordered_by_created_at_desc(orders_dataset):
    orders = await service.get_orders()
    for prev, curr in zip(orders, orders[1:]):  # noqa: B905
        assert prev.created_at >= curr.created_at


async def test_get_orders_empty():
    orders = await service.get_orders()
    assert orders == []


async def test_get_order_with_payments_loaded():
    order = await create_order()
    await create_payment(order=order, amount=Decimal("100.00"))
    result = await service.get_order_with_payments(order.id)
    assert result.id == order.id
    assert len(result.payments) == 1


async def test_get_order_with_no_payments():
    order = await create_order()
    result = await service.get_order_with_payments(order.id)
    assert len(result.payments) == 0


async def test_recalculate_not_paid_when_no_payments():
    order = await create_order(amount=Decimal("1000.00"))
    result = await service.recalculate_payment_status(order)
    assert result.payment_status == PaymentStatus.NOT_PAID


async def test_recalculate_partially_paid():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("500.00"))
    result = await service.recalculate_payment_status(order)
    assert result.payment_status == PaymentStatus.PARTIALLY_PAID


async def test_recalculate_fully_paid():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("1000.00"))
    result = await service.recalculate_payment_status(order)
    assert result.payment_status == PaymentStatus.PAID


async def test_recalculate_ignores_refunded():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(
        order=order,
        amount=Decimal("1000.00"),
        operation_status=PaymentOperationStatus.REFUNDED,
    )
    result = await service.recalculate_payment_status(order)
    assert result.payment_status == PaymentStatus.NOT_PAID


async def test_recalculate_ignores_pending():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(
        order=order,
        amount=Decimal("500.00"),
        payment_type=PaymentType.ACQUIRING,
        operation_status=PaymentOperationStatus.PENDING,
    )
    result = await service.recalculate_payment_status(order)
    assert result.payment_status == PaymentStatus.NOT_PAID


async def test_recalculate_sums_multiple_deposited():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("400.00"))
    await create_payment(order=order, amount=Decimal("600.00"))
    result = await service.recalculate_payment_status(order)
    assert result.payment_status == PaymentStatus.PAID


async def test_recalculate_persists_to_db():
    order = await create_order(amount=Decimal("1000.00"))
    await create_payment(order=order, amount=Decimal("1000.00"))
    await service.recalculate_payment_status(order)
    refreshed = await Order.get(id=order.id)
    assert refreshed.payment_status == PaymentStatus.PAID


async def test_api_list_orders(client, orders_dataset):
    response = await client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(ORDER_DATASET)
    assert len(data["items"]) == len(ORDER_DATASET)


async def test_api_list_orders_empty(client):
    response = await client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


async def test_api_order_response_fields(client, orders_dataset):
    response = await client.get("/orders")
    item = response.json()["items"][0]
    assert "id" in item
    assert "amount" in item
    assert "payment_status" in item
    assert "created_at" in item
    assert "updated_at" in item


async def test_api_get_existing_order(client, orders_dataset):
    order = orders_dataset[0]
    response = await client.get(f"/orders/{order.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order.id
    assert data["payment_status"] == order.payment_status.value


async def test_api_get_nonexistent_order(client):
    response = await client.get("/orders/99999")
    assert response.status_code == 404
