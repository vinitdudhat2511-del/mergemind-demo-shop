"""Run a sample order end to end."""

from shop.orders import process_order

if __name__ == "__main__":
    order_id = process_order("alice@example.com", "demo-password", "laptop", 1, 999.0)
    print(f"Order {order_id} placed")
