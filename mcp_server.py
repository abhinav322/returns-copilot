import sys
from contextlib import redirect_stdout
from backend.returns_logic import RETURN_WINDOW_DAYS

from backend.courier_client import (
    get_shipment,
    ShipmentNotFoundError,
    CourierServiceError,
)
from mcp.server import MCPServer

from backend.database import SessionLocal
from backend.services import evaluate_return_for_order

# Create the MCP server
mcp = MCPServer("Returns Copilot")


@mcp.tool()
def check_return_eligibility(order_number: str) -> dict:
    """Check whether an order is eligible for return."""

    with SessionLocal() as db:
        result = evaluate_return_for_order(
            db=db,
            order_number=order_number
        )

    if result is None:
        return {
            "order_number": order_number,
            "found": False,
            "message": "Order not found"
        }

    return {
        "found": True,
        "return_window_days": RETURN_WINDOW_DAYS,
        **result
    }


@mcp.tool()
def track_shipment(order_number: str) -> dict:
    """Retrieve shipment tracking information for an order."""

    try:
        with redirect_stdout(sys.stderr):
            shipment = get_shipment(order_number)

        return {
            "found": True,
            **shipment
        }

    except ShipmentNotFoundError:
        return {
            "order_number": order_number,
            "found": False,
            "message": "Shipment not found"
        }

    except CourierServiceError as error:
        return {
            "order_number": order_number,
            "found": False,
            "message": "Courier service unavailable",
            "details": str(error)
        }


@mcp.tool()
def search_policy(
    query: str,
    region: str = "UK"
) -> dict:
    """Search return policy documents for relevant information."""

    if not query.strip():
        return {
            "found": False,
            "message": "Search query cannot be empty"
        }

    with redirect_stdout(sys.stderr):
        from backend.rag.hybrid_search import (
            hybrid_search_policy_chunks,
        )

        results = hybrid_search_policy_chunks(
            query=query,
            region=region,
            top_k=3
        )

    return {
        "query": query,
        "region": region,
        "found": bool(results),
        "results": results
    }


if __name__ == "__main__":
    mcp.run()
