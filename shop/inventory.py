"""A very small in-memory inventory."""

_DEFAULT_STOCK = {"laptop": 5, "mouse": 20, "keyboard": 0}
_STOCK = dict(_DEFAULT_STOCK)


def check_stock(item, quantity=1):
    """Return True if enough units of an item are available."""
    return _STOCK.get(item, 0) >= quantity


def reserve_stock(item, quantity=1):
    """Remove units from stock."""
    if _STOCK.get(item, 0) < quantity:
        raise ValueError(f"not enough stock for {item}")
    _STOCK[item] -= quantity


def reset_stock():
    """Restore the default stock levels (used by tests)."""
    _STOCK.clear()
    _STOCK.update(_DEFAULT_STOCK)
