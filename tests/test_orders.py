import pytest

from core.exceptions import NotFoundError
from domains.orders.repository import OrderRepository
from domains.orders.schemas import OrderCreate, OrderUpdate
from domains.orders.service import OrderService
from domains.products.repository import ProductRepository
from domains.products.schemas import ProductCreate
from domains.products.service import ProductService
from domains.users.repository import UserRepository
from domains.users.schemas import UserCreate
from domains.users.service import UserService


@pytest.fixture()
def users(db_session) -> UserService:
    return UserService(UserRepository(db_session))


@pytest.fixture()
def products(db_session) -> ProductService:
    return ProductService(ProductRepository(db_session))


@pytest.fixture()
def orders(db_session) -> OrderService:
    return OrderService(
        orders=OrderRepository(db_session),
        users=UserRepository(db_session),
        products=ProductRepository(db_session),
    )


def test_create_order_happy_path(orders, users, products):
    user = users.create_user(UserCreate(name="Riley", email="riley@example.com"))
    product = products.create_product(
        ProductCreate(title="Keyboard", price=79.99, stock=12)
    )
    order = orders.create_order(
        OrderCreate(user_id=user.id, product_id=product.id, quantity=2)
    )
    assert order.id == 1
    assert order.quantity == 2


def test_create_order_with_unknown_user_raises_not_found(orders, users, products):
    user = users.create_user(UserCreate(name="Riley", email="riley@example.com"))
    product = products.create_product(
        ProductCreate(title="Keyboard", price=79.99, stock=12)
    )
    with pytest.raises(NotFoundError, match="user 999 not found"):
        orders.create_order(
            OrderCreate(user_id=999, product_id=product.id, quantity=1)
        )


def test_create_order_with_soft_deleted_product_rejected(orders, users, products):
    user = users.create_user(UserCreate(name="Riley", email="riley@example.com"))
    product = products.create_product(
        ProductCreate(title="Keyboard", price=79.99, stock=12)
    )
    products.delete_product(product.id)
    with pytest.raises(NotFoundError, match="product"):
        orders.create_order(
            OrderCreate(user_id=user.id, product_id=product.id, quantity=1)
        )


def test_update_order_retargeted_to_missing_user_rejected(orders, users, products):
    user = users.create_user(UserCreate(name="Riley", email="riley@example.com"))
    product = products.create_product(
        ProductCreate(title="Keyboard", price=79.99, stock=12)
    )
    order = orders.create_order(
        OrderCreate(user_id=user.id, product_id=product.id, quantity=2)
    )
    with pytest.raises(NotFoundError, match="product 42 not found"):
        orders.update_order(order.id, OrderUpdate(product_id=42))


def test_update_order_quantity_succeeds_after_user_soft_deleted(orders, users, products):
    user = users.create_user(UserCreate(name="Riley", email="riley@example.com"))
    product = products.create_product(
        ProductCreate(title="Keyboard", price=79.99, stock=12)
    )
    order = orders.create_order(
        OrderCreate(user_id=user.id, product_id=product.id, quantity=2)
    )
    users.delete_user(user.id)
    updated = orders.update_order(order.id, OrderUpdate(quantity=7))
    assert updated.quantity == 7


def test_soft_deleted_order_is_hidden(orders, users, products):
    user = users.create_user(UserCreate(name="Riley", email="riley@example.com"))
    product = products.create_product(
        ProductCreate(title="Keyboard", price=79.99, stock=12)
    )
    order = orders.create_order(
        OrderCreate(user_id=user.id, product_id=product.id, quantity=2)
    )
    orders.delete_order(order.id)
    with pytest.raises(NotFoundError):
        orders.get_order(order.id)
    assert orders.list_orders() == []
