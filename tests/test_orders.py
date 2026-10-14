import pytest

from shop import inventory
from shop.orders import process_order


def test_process_order_returns_id():
    order_id = process_order("alice@example.com", "demo-password", "laptop", 1, 999.0)
    assert order_id >= 1001


def test_bad_password_rejected():
    with pytest.raises(PermissionError):
        process_order("alice@example.com", "wrong", "laptop", 1, 999.0)


def test_failed_login_does_not_reserve_stock():
    with pytest.raises(PermissionError):
        process_order("alice@example.com", "wrong", "laptop", 5, 999.0)
    assert inventory.check_stock("laptop", 5)
