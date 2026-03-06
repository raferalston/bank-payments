from fastapi import APIRouter, Depends

from src.orders import service
from src.orders.dependencies import valid_order_id
from src.orders.models import Order
from src.orders.schemas import OrderListResponse, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=OrderListResponse)
async def get_orders():
    orders = await service.get_orders()
    return OrderListResponse(
        items=[OrderResponse.model_validate(order, from_attributes=True) for order in orders],
        total=len(orders),
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order: Order = Depends(valid_order_id)):
    return OrderResponse.model_validate(order, from_attributes=True)
