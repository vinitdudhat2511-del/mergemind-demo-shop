"""Customer notifications."""


def send_receipt(email, order_id, total):
    """Pretend to email a receipt and return the message text."""
    message = f"Receipt for order {order_id}: total {total:.2f}"
    print(f"[email -> {email}] {message}")
    return message
