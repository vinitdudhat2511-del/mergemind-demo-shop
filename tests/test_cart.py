from shop.cart import Cart


def test_cart_count():
    cart = Cart()
    cart.add("mouse", 2)
    cart.add("laptop")
    assert cart.count() == 3
