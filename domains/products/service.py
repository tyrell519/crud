from core.exceptions import NotFoundError
from domains.products.models import Product
from domains.products.repository import ProductRepository
from domains.products.schemas import ProductCreate, ProductUpdate


class ProductService:
    """Business rules for the products domain."""

    def __init__(self, products: ProductRepository):
        self.products = products

    def create_product(self, data: ProductCreate) -> Product:
        return self.products.create(**data.model_dump())

    def get_product(self, product_id: int) -> Product:
        product = self.products.get_active_by_id(product_id)
        if product is None:
            raise NotFoundError("product not found")
        return product

    def list_products(self) -> list[Product]:
        return self.products.list_active()

    def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        product = self.get_product(product_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        return self.products.save(product)

    def delete_product(self, product_id: int) -> None:
        product = self.get_product(product_id)
        self.products.soft_delete(product)
