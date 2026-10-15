import httpx
import pytest

from backend import courier_client

from backend.courier_client import (
    CourierServiceError,
    ShipmentNotFoundError,
    get_shipment,
)


def test_successful_shipment(
    monkeypatch,
):

    call_count = 0


    def fake_get(
        url,
        timeout,
    ):

        nonlocal call_count

        call_count += 1

        request = httpx.Request(
            "GET",
            url,
        )

        return httpx.Response(
            status_code=200,
            json={
                "order_number":
                    "ORD-2001",

                "tracking_number":
                    "TRK-TEST-001",

                "status":
                    "in_transit",

                "current_location":
                    "Test Depot",

                "estimated_delivery":
                    "2026-10-16",

                "last_updated":
                    "2026-10-14T10:00:00",
            },
            request=request,
        )


    monkeypatch.setattr(
        courier_client.httpx,
        "get",
        fake_get,
    )


    result = get_shipment(
        "ORD-2001"
    )


    assert (
        result["order_number"]
        == "ORD-2001"
    )

    assert (
        result["status"]
        == "in_transit"
    )

    assert call_count == 1


def test_404_does_not_retry(
    monkeypatch,
):

    call_count = 0


    def fake_get(
        url,
        timeout,
    ):

        nonlocal call_count

        call_count += 1

        request = httpx.Request(
            "GET",
            url,
        )

        return httpx.Response(
            status_code=404,
            json={
                "detail":
                    "Shipment not found"
            },
            request=request,
        )


    monkeypatch.setattr(
        courier_client.httpx,
        "get",
        fake_get,
    )


    with pytest.raises(
        ShipmentNotFoundError
    ):

        get_shipment(
            "ORD-9999"
        )


    assert call_count == 1


def test_503_retries_then_succeeds(
    monkeypatch,
):

    call_count = 0


    def fake_get(
        url,
        timeout,
    ):

        nonlocal call_count

        call_count += 1

        request = httpx.Request(
            "GET",
            url,
        )


        if call_count < 3:

            return httpx.Response(
                status_code=503,
                json={
                    "detail":
                        "Service unavailable"
                },
                request=request,
            )


        return httpx.Response(
            status_code=200,
            json={
                "order_number":
                    "ORD-2002",

                "tracking_number":
                    "TRK-TEST-002",

                "status":
                    "delayed",

                "current_location":
                    "Test Hub",

                "estimated_delivery":
                    "2026-10-18",

                "last_updated":
                    "2026-10-14T11:00:00",
            },
            request=request,
        )


    monkeypatch.setattr(
        courier_client.httpx,
        "get",
        fake_get,
    )


    monkeypatch.setattr(
        courier_client.time,
        "sleep",
        lambda seconds: None,
    )


    result = get_shipment(
        "ORD-2002"
    )


    assert call_count == 3

    assert (
        result["status"]
        == "delayed"
    )


def test_timeout_retries_three_times(
    monkeypatch,
):

    call_count = 0


    def fake_get(
        url,
        timeout,
    ):

        nonlocal call_count

        call_count += 1

        request = httpx.Request(
            "GET",
            url,
        )

        raise httpx.ReadTimeout(
            "Courier timed out",
            request=request,
        )


    monkeypatch.setattr(
        courier_client.httpx,
        "get",
        fake_get,
    )


    monkeypatch.setattr(
        courier_client.time,
        "sleep",
        lambda seconds: None,
    )


    with pytest.raises(
        CourierServiceError
    ) as error_info:

        get_shipment(
            "ORD-2003"
        )


    assert call_count == 3

    assert (
        "after 3 attempts"
        in str(
            error_info.value
        )
    )