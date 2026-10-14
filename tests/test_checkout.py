import pytest

from shop.checkout import OutOfStockError, checkout


def test_checkout_total_includes_tax():
    assert checkout("mouse", 2, 50.0) == 118.0


def test_checkout_out_of_stock():
    with pytest.raises(OutOfStockError):
        checkout("keyboard", 1, 30.0)
