from datetime import date

from sqlalchemy import select

from backend.database import SessionLocal
from backend.db_models import Order


mock_orders = [
    {
        "order_number": "ORD-1001",
        "customer_email": "alice@example.com",
        "product_name": "Linen Shirt",
        "delivered_at": date(2026, 9, 12),
        "item_condition": "unused",
        "final_sale": False,
        "region": "UK",
    },
    {
        "order_number": "ORD-1002",
        "customer_email": "bob@example.com",
        "product_name": "Denim Jacket",
        "delivered_at": date(2026, 7, 30),
        "item_condition": "unused",
        "final_sale": False,
        "region": "UK",
    },
    {
        "order_number": "ORD-1003",
        "customer_email": "carol@example.com",
        "product_name": "Sale Dress",
        "delivered_at": date(2026, 9, 15),
        "item_condition": "unused",
        "final_sale": True,
        "region": "EU",
    },
    {
        "order_number": "ORD-1004",
        "customer_email": "dan@example.com",
        "product_name": "Cotton T Shirt",
        "delivered_at": date(2026, 9, 18),
        "item_condition": "used",
        "final_sale": False,
        "region": "UK",
    },
]


def seed_orders():
    db = SessionLocal()

    try:
        for order_data in mock_orders:
            existing_order = db.scalar(
                select(Order).where(
                    Order.order_number
                    == order_data["order_number"]
                )
            )

            if existing_order:
                print(
                    f"{order_data['order_number']} already exists"
                )
                continue

            order = Order(**order_data)

            db.add(order)

        db.commit()

        print("Mock orders inserted.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_orders()