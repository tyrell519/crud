from fastapi import APIRouter, Depends

from domains.orders.dependencies import get_order_service
from domains.orders.schemas import OrderCreate, OrderOut, OrderUpdate
from domains.orders.service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", status_code=201, response_model=OrderOut)
def create_order(payload: OrderCreate, service: OrderService = Depends(get_order_service)):
    return service.create_order(payload)


@router.get("", response_model=list[OrderOut])
def list_orders(service: OrderService = Depends(get_order_service)):
    return service.list_orders()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, service: OrderService = Depends(get_order_service)):
    return service.get_order(order_id)


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    service: OrderService = Depends(get_order_service),
):
    return service.update_order(order_id, payload)


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, service: OrderService = Depends(get_order_service)):
    service.delete_order(order_id)
