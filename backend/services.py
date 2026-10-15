from datetime import date

from sqlalchemy.orm import Session

from backend.repositories import get_order_by_number
from backend.returns_logic import check_return_eligibility


def evaluate_return_for_order(
    db: Session,
    order_number: str,
    as_of: date | None = None
):
    order = get_order_by_number(
        db,
        order_number
    )

    if order is None:
        return None

    current_date = as_of or date.today()

    days_since_delivery = (
        current_date - order.delivered_at
    ).days

    result = check_return_eligibility(
        days_since_delivery=days_since_delivery,
        item_condition=order.item_condition,
        final_sale=order.final_sale
    )

    return {
        "order_number": order.order_number,
        "days_since_delivery": days_since_delivery,
        "eligible": result["eligible"],
        "reason": result["reason"]
    }