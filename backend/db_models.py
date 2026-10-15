from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True
    )

    customer_email: Mapped[str] = mapped_column(
        String(255)
    )

    product_name: Mapped[str] = mapped_column(
        String(255)
    )

    delivered_at: Mapped[date] = mapped_column(
        Date
    )

    item_condition: Mapped[str] = mapped_column(
        String(20)
    )

    final_sale: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    region: Mapped[str] = mapped_column(
        String(10)
    )