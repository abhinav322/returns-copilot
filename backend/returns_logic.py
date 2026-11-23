
RETURN_WINDOW_DAYS = 30

def check_return_eligibility(
    days_since_delivery: int,
    item_condition: str,
    final_sale: bool
):
    if days_since_delivery > RETURN_WINDOW_DAYS:
        return {
            "eligible": False,
            "reason": "Return window exceeded"
        }

    if item_condition != "unused":
        return {
            "eligible": False,
            "reason": "Item must be unused"
        }

    if final_sale:
        return {
            "eligible": False,
            "reason": "Final sale items cannot be returned"
        }

    return {
        "eligible": True,
        "reason": "Return meets policy requirements"
    }