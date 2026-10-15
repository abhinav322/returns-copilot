from typing import (
    Literal,
    TypedDict,
)

from uuid import uuid4

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from backend.intent_classifier import (
    classify_intent,
)

from backend.workflow.order_return_graph import (
    start_order_return_workflow,
)

from backend.workflow.shipment_status_graph import (
    run_shipment_workflow,
)


class SupportRouterState(
    TypedDict,
    total=False,
):
    order_number: str
    question: str
    thread_id: str

    intent: str
    status: str

    answer: str
    draft_answer: str

    decision: dict

    validation_issues: list[str]
    human_approved: bool | None

    sources: list[dict]

    shipment: dict
    courier_status: str
    courier_error: str


def build_support_router_graph():

    def classify_request(
        state: SupportRouterState,
    ) -> dict:

        intent = classify_intent(
            state["question"]
        )

        return {
            "intent": intent
        }


    def route_intent(
        state: SupportRouterState,
    ) -> Literal[
        "return",
        "wismo",
        "unknown",
    ]:

        intent = state[
            "intent"
        ]

        if intent == "RETURN":

            return "return"

        if intent == "WISMO":

            return "wismo"

        return "unknown"


    def handle_return(
        state: SupportRouterState,
    ) -> dict:

        result = (
            start_order_return_workflow(
                order_number=
                    state["order_number"],

                question=
                    state["question"],

                thread_id=
                    state["thread_id"],
            )
        )


        if "__interrupt__" in result:

            interrupt_data = (
                result[
                    "__interrupt__"
                ][0].value
            )

            return {
                "status":
                    "pending_review",

                "draft_answer":
                    interrupt_data.get(
                        "draft_answer"
                    ),

                "decision":
                    result.get(
                        "decision"
                    ),

                "validation_issues":
                    interrupt_data.get(
                        "validation_issues",
                        [],
                    ),

                "human_approved":
                    None,

                "sources":
                    interrupt_data.get(
                        "sources",
                        [],
                    ),
            }


        return {
            "status":
                "completed",

            "answer":
                result.get(
                    "answer"
                ),

            "decision":
                result.get(
                    "decision"
                ),

            "validation_issues":
                result.get(
                    "validation_issues",
                    [],
                ),

            "human_approved":
                result.get(
                    "human_approved"
                ),

            "sources":
                result.get(
                    "sources",
                    [],
                ),
        }


    def handle_wismo(
        state: SupportRouterState,
    ) -> dict:

        result = (
            run_shipment_workflow(
                order_number=
                    state["order_number"],

                question=
                    state["question"],
            )
        )

        return {
            "status":
                "completed",

            "answer":
                result.get(
                    "answer"
                ),

            "shipment":
                result.get(
                    "shipment"
                ),

            "courier_status":
                result.get(
                    "courier_status",
                    "",
                ),

            "courier_error":
                result.get(
                    "courier_error",
                    "",
                ),
        }


    def handle_unknown(
        state: SupportRouterState,
    ) -> dict:

        return {
            "status":
                "completed",

            "answer":
                (
                    "I can currently help with "
                    "return eligibility and "
                    "shipment tracking. "
                    "Please ask about a return "
                    "or the status of an order."
                ),
        }


    builder = StateGraph(
        SupportRouterState
    )


    builder.add_node(
        "classify_request",
        classify_request,
    )

    builder.add_node(
        "handle_return",
        handle_return,
    )

    builder.add_node(
        "handle_wismo",
        handle_wismo,
    )

    builder.add_node(
        "handle_unknown",
        handle_unknown,
    )


    builder.add_edge(
        START,
        "classify_request",
    )


    builder.add_conditional_edges(
        "classify_request",
        route_intent,
        {
            "return":
                "handle_return",

            "wismo":
                "handle_wismo",

            "unknown":
                "handle_unknown",
        },
    )


    builder.add_edge(
        "handle_return",
        END,
    )

    builder.add_edge(
        "handle_wismo",
        END,
    )

    builder.add_edge(
        "handle_unknown",
        END,
    )


    return builder.compile()


SUPPORT_ROUTER_GRAPH = (
    build_support_router_graph()
)


def run_support_request(
    order_number: str,
    question: str,
    thread_id: str | None = None,
) -> dict:

    if thread_id is None:

        thread_id = str(
            uuid4()
        )

    initial_state = {
        "order_number":
            order_number,

        "question":
            question,

        "thread_id":
            thread_id,
    }


    return SUPPORT_ROUTER_GRAPH.invoke(
        initial_state
    )