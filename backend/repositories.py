from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db_models import Order


def get_order_by_number(
    db: Session,
    order_number: str
) -> Order | None:

    statement = select(Order).where(
        Order.order_number == order_number
    )

    return db.scalar(statement)