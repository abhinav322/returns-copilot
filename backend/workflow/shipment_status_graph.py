from typing import (
    Literal,
    TypedDict,
)

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from backend.courier_client import (
    CourierServiceError,
    ShipmentNotFoundError,
    get_shipment,
)

from backend.rag.ollama_client import (
    generate_response,
)


class ShipmentState(
    TypedDict,
    total=False,
):
    order_number: str
    question: str

    shipment: dict

    courier_status: str
    courier_error: str

    answer: str


def build_shipment_graph():

    def fetch_shipment(
        state: ShipmentState,
    ) -> dict:

        try:

            shipment = get_shipment(
                state["order_number"]
            )

            return {
                "shipment":
                    shipment,

                "courier_status":
                    "success",

                "courier_error":
                    "",
            }

        except ShipmentNotFoundError as error:

            return {
                "courier_status":
                    "not_found",

                "courier_error":
                    str(error),
            }

        except CourierServiceError as error:

            return {
                "courier_status":
                    "unavailable",

                "courier_error":
                    str(error),
            }


    def route_after_courier(
        state: ShipmentState,
    ) -> Literal[
        "success",
        "not_found",
        "unavailable",
    ]:

        status = state[
            "courier_status"
        ]

        if status == "success":

            return "success"

        if status == "not_found":

            return "not_found"

        return "unavailable"


    def draft_shipment_answer(
        state: ShipmentState,
    ) -> dict:

        shipment = state[
            "shipment"
        ]

        prompt = f"""
You are a customer support assistant.

Answer the customer's shipment question
using ONLY the shipment data below.

Important rules:
- Do not invent shipment information.
- Do not invent a courier company.
- Do not change the shipment status.
- Be concise and customer friendly.
- If an estimated delivery date exists,
  mention it.
- If estimated delivery is null,
  do not invent one.

CUSTOMER QUESTION:
{state['question']}

SHIPMENT DATA:
Order number:
{shipment['order_number']}

Tracking number:
{shipment['tracking_number']}

Status:
{shipment['status']}

Current location:
{shipment['current_location']}

Estimated delivery:
{shipment['estimated_delivery']}

Last updated:
{shipment['last_updated']}
"""

        answer = generate_response(
            prompt
        )

        return {
            "answer":
                answer
        }


    def shipment_not_found(
        state: ShipmentState,
    ) -> dict:

        return {
            "answer": (
                "I couldn't find shipment "
                "information for order "
                f"{state['order_number']}."
            )
        }


    def courier_unavailable(
        state: ShipmentState,
    ) -> dict:

        return {
            "answer": (
                "Shipment tracking is "
                "temporarily unavailable. "
                "Please try again shortly."
            )
        }


    builder = StateGraph(
        ShipmentState
    )


    builder.add_node(
        "fetch_shipment",
        fetch_shipment,
    )

    builder.add_node(
        "draft_shipment_answer",
        draft_shipment_answer,
    )

    builder.add_node(
        "shipment_not_found",
        shipment_not_found,
    )

    builder.add_node(
        "courier_unavailable",
        courier_unavailable,
    )


    builder.add_edge(
        START,
        "fetch_shipment",
    )


    builder.add_conditional_edges(
        "fetch_shipment",
        route_after_courier,
        {
            "success":
                "draft_shipment_answer",

            "not_found":
                "shipment_not_found",

            "unavailable":
                "courier_unavailable",
        },
    )


    builder.add_edge(
        "draft_shipment_answer",
        END,
    )

    builder.add_edge(
        "shipment_not_found",
        END,
    )

    builder.add_edge(
        "courier_unavailable",
        END,
    )


    return builder.compile()


SHIPMENT_GRAPH = (
    build_shipment_graph()
)


def run_shipment_workflow(
    order_number: str,
    question: str,
) -> dict:

    initial_state = {
        "order_number":
            order_number,

        "question":
            question,
    }

    return SHIPMENT_GRAPH.invoke(
        initial_state
    )