"""Order processing: the top of the call chain."""

from itertools import count

from shop.auth import authenticate
from shop.checkout import checkout
from shop.notifications import send_receipt

_order_ids = count(1001)


def process_order(email, password, item, quantity, unit_price):
    """Authenticate, check out and send a receipt. Returns the order id."""
    if not authenticate(email, password):
        raise PermissionError("invalid credentials")

    total = checkout(item, quantity, unit_price)
    order_id = next(_order_ids)
    send_receipt(email, order_id, total)
    return order_id
