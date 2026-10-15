from datetime import datetime
from typing import Literal

from fastapi import (
    FastAPI,
    HTTPException,
)

from pydantic import BaseModel


app = FastAPI(
    title="Mock Courier API",
    version="0.1.0",
)


class ShipmentResponse(BaseModel):
    order_number: str

    tracking_number: str

    status: Literal[
        "in_transit",
        "delayed",
        "out_for_delivery",
        "delivered",
    ]

    current_location: str

    estimated_delivery: str | None

    last_updated: datetime


SHIPMENTS = {

    "ORD-2001": {
        "order_number": "ORD-2001",
        "tracking_number": "TRK-UK-2001",
        "status": "in_transit",
        "current_location": (
            "Birmingham Distribution Centre"
        ),
        "estimated_delivery": "2026-10-16",
        "last_updated": (
            "2026-10-14T09:30:00"
        ),
    },

    "ORD-2002": {
        "order_number": "ORD-2002",
        "tracking_number": "TRK-UK-2002",
        "status": "delayed",
        "current_location": (
            "Manchester Distribution Centre"
        ),
        "estimated_delivery": "2026-10-18",
        "last_updated": (
            "2026-10-14T08:15:00"
        ),
    },

    "ORD-2003": {
        "order_number": "ORD-2003",
        "tracking_number": "TRK-EU-2003",
        "status": "out_for_delivery",
        "current_location": (
            "Amsterdam Local Depot"
        ),
        "estimated_delivery": "2026-10-14",
        "last_updated": (
            "2026-10-14T07:45:00"
        ),
    },

    "ORD-2004": {
        "order_number": "ORD-2004",
        "tracking_number": "TRK-UK-2004",
        "status": "delivered",
        "current_location": "Leeds",
        "estimated_delivery": None,
        "last_updated": (
            "2026-10-13T15:20:00"
        ),
    },
}


@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "service": "mock-courier",
    }


@app.get(
    "/shipments/{order_number}",
    response_model=ShipmentResponse,
)
def get_shipment(
    order_number: str,
):

    shipment = SHIPMENTS.get(
        order_number
    )

    if shipment is None:

        raise HTTPException(
            status_code=404,
            detail="Shipment not found",
        )

    return shipment