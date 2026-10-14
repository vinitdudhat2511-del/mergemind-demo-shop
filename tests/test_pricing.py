from shop.pricing import apply_discount, calculate_price, calculate_tax, order_total


def test_calculate_tax():
    assert calculate_tax(100) == 18.0


def test_calculate_price():
    assert calculate_price(100, 18) == 118.0


def test_apply_discount():
    assert apply_discount(200, 10) == 180.0


def test_order_total():
    assert order_total(100) == 118.0
    assert order_total(200, 10) == 212.4
