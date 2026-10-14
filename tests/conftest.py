import pytest

from shop import inventory


@pytest.fixture(autouse=True)
def fresh_stock():
    inventory.reset_stock()
    yield
    inventory.reset_stock()
