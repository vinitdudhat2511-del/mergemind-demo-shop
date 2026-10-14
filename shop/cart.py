"""Shopping cart."""


class Cart:
    """Collects items before checkout."""

    def __init__(self):
        self.items = []

    def add(self, item, quantity=1):
        """Add an item to the cart."""
        self.items.append((item, quantity))

    def count(self):
        """Return the total number of units in the cart."""
        return sum(quantity for _, quantity in self.items)
