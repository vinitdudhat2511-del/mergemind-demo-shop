"""Checkout logic: stock check, pricing and reservation."""

from shop import inventory
from shop.pricing import order_total


class OutOfStockError(Exception):
    """Raised when an item cannot be fulfilled."""


def checkout(item, quantity, unit_price):
    """Validate stock, compute the total and reserve the items."""
    if not inventory.check_stock(item, quantity):
        raise OutOfStockError(f"{item} is out of stock")

    total = order_total(unit_price * quantity)

    inventory.reserve_stock(item, quantity)
    return total
