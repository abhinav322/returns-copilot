from datetime import (
    date,
    timedelta,
)

import pytest

from fastapi.testclient import (
    TestClient,
)

from backend.app import app

from backend.database import (
    SessionLocal,
)

from backend.repositories import (
    get_order_by_number,
)


client = TestClient(app)


@pytest.fixture
def stable_order_dates():
    """
    Temporarily set delivery dates so each
    test always reaches the business-rule
    branch it is intended to test.

    After the test finishes, restore the
    original database values.
    """

    db = SessionLocal()

    order_numbers = [
        "ORD-1001",
        "ORD-1002",
        "ORD-1003",
        "ORD-1004",
    ]

    original_dates = {}

    try:

        for order_number in order_numbers:

            order = get_order_by_number(
                db,
                order_number,
            )

            original_dates[
                order_number
            ] = order.delivered_at


        today = date.today()


        # Eligible:
        # safely inside 30-day window.
        order_1001 = get_order_by_number(
            db,
            "ORD-1001",
        )

        order_1001.delivered_at = (
            today - timedelta(days=10)
        )


        # Expired:
        # definitely outside 30-day window.
        order_1002 = get_order_by_number(
            db,
            "ORD-1002",
        )

        order_1002.delivered_at = (
            today - timedelta(days=40)
        )


        # Final sale:
        # keep inside return window so the
        # final-sale rule is actually tested.
        order_1003 = get_order_by_number(
            db,
            "ORD-1003",
        )

        order_1003.delivered_at = (
            today - timedelta(days=10)
        )


        # Used item:
        # keep inside return window so the
        # item-condition rule is actually tested.
        order_1004 = get_order_by_number(
            db,
            "ORD-1004",
        )

        order_1004.delivered_at = (
            today - timedelta(days=10)
        )


        db.commit()

        yield


    finally:

        for (
            order_number,
            original_date,
        ) in original_dates.items():

            order = get_order_by_number(
                db,
                order_number,
            )

            order.delivered_at = (
                original_date
            )


        db.commit()

        db.close()


def test_health_check():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok"
    }


def test_existing_order():

    response = client.get(
        "/orders/ORD-1001"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["order_number"]
        == "ORD-1001"
    )

    assert (
        data["product_name"]
        == "Linen Shirt"
    )


def test_missing_order_returns_404():

    response = client.get(
        "/orders/ORD-9999"
    )

    assert response.status_code == 404


def test_eligible_return(
    stable_order_dates,
):

    response = client.post(
        "/returns/check",
        json={
            "order_number":
                "ORD-1001"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["eligible"]
        is True
    )

    assert (
        data["reason"]
        == "Return meets policy requirements"
    )

    assert (
        data["days_since_delivery"]
        == 10
    )


def test_expired_return(
    stable_order_dates,
):

    response = client.post(
        "/returns/check",
        json={
            "order_number":
                "ORD-1002"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["eligible"]
        is False
    )

    assert (
        data["reason"]
        == "Return window exceeded"
    )

    assert (
        data["days_since_delivery"]
        == 40
    )


def test_final_sale_return(
    stable_order_dates,
):

    response = client.post(
        "/returns/check",
        json={
            "order_number":
                "ORD-1003"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["eligible"]
        is False
    )

    assert (
        data["reason"]
        == "Final sale items cannot be returned"
    )

    assert (
        data["days_since_delivery"]
        == 10
    )


def test_used_item_return(
    stable_order_dates,
):

    response = client.post(
        "/returns/check",
        json={
            "order_number":
                "ORD-1004"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["eligible"]
        is False
    )

    assert (
        data["reason"]
        == "Item must be unused"
    )

    assert (
        data["days_since_delivery"]
        == 10
    )