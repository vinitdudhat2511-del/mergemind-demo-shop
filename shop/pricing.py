"""Pricing helpers."""

TAX_RATE = 0.18


def calculate_tax(price, rate=TAX_RATE):
    """Return the tax amount for a price."""
    return round(price * rate, 2)


def calculate_price(price, tax):
    """Return the price including tax."""
    return round(price + tax, 2)


def apply_discount(price, percent):
    """Return the price after a percentage discount."""
    if percent < 0:
        raise ValueError("percent must be >= 0")
    discounted = price * (1 - percent / 100)
    return round(discounted, 2)


def order_total(subtotal, discount_percent=0):
    """Apply the discount, add tax and return the final amount."""
    discounted = apply_discount(subtotal, discount_percent)
    tax = calculate_tax(discounted)
    total = calculate_price(discounted, tax)

    return total
