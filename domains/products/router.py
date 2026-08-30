from fastapi import APIRouter, Depends

from domains.products.dependencies import get_product_service
from domains.products.schemas import ProductCreate, ProductOut, ProductUpdate
from domains.products.service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", status_code=201, response_model=ProductOut)
def create_product(
    payload: ProductCreate, service: ProductService = Depends(get_product_service)
):
    return service.create_product(payload)


@router.get("", response_model=list[ProductOut])
def list_products(service: ProductService = Depends(get_product_service)):
    return service.list_products()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int, service: ProductService = Depends(get_product_service)
):
    return service.get_product(product_id)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    return service.update_product(product_id, payload)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int, service: ProductService = Depends(get_product_service)
):
    service.delete_product(product_id)
