from core.exceptions import NotFoundError
from domains.orders.models import Order
from domains.orders.repository import OrderRepository
from domains.orders.schemas import OrderCreate, OrderUpdate
from domains.products.repository import ProductRepository
from domains.users.repository import UserRepository


class OrderService:
    """Business rules for the orders domain.

    Cross-domain invariants (an order must reference a live user and
    product) are enforced here, via read access to the other domains'
    repositories.
    """

    def __init__(
        self,
        orders: OrderRepository,
        users: UserRepository,
        products: ProductRepository,
    ):
        self.orders = orders
        self.users = users
        self.products = products

    def create_order(self, data: OrderCreate) -> Order:
        self._ensure_targets_exist(data.user_id, data.product_id)
        return self.orders.create(**data.model_dump())

    def get_order(self, order_id: int) -> Order:
        order = self.orders.get_active_by_id(order_id)
        if order is None:
            raise NotFoundError("order not found")
        return order

    def list_orders(self) -> list[Order]:
        return self.orders.list_active()

    def update_order(self, order_id: int, data: OrderUpdate) -> Order:
        order = self.get_order(order_id)
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            return order
        if "user_id" in changes and self.users.get_active_by_id(changes["user_id"]) is None:
            raise NotFoundError(f"user {changes['user_id']} not found")
        if "product_id" in changes and self.products.get_active_by_id(changes["product_id"]) is None:
            raise NotFoundError(f"product {changes['product_id']} not found")
        for field, value in changes.items():
            setattr(order, field, value)
        return self.orders.save(order)

    def delete_order(self, order_id: int) -> None:
        order = self.get_order(order_id)
        self.orders.soft_delete(order)

    def _ensure_targets_exist(self, user_id: int, product_id: int) -> None:
        if self.users.get_active_by_id(user_id) is None:
            raise NotFoundError(f"user {user_id} not found")
        if self.products.get_active_by_id(product_id) is None:
            raise NotFoundError(f"product {product_id} not found")
