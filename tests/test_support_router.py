from backend.workflow import (
    support_router_graph,
)


def test_wismo_route(
    monkeypatch,
):

    def fake_classify_intent(
        question: str,
    ) -> str:

        return "WISMO"


    def fake_shipment_workflow(
        order_number: str,
        question: str,
    ) -> dict:

        return {
            "order_number":
                order_number,

            "question":
                question,

            "shipment": {
                "order_number":
                    order_number,

                "tracking_number":
                    "TEST-TRACK-001",

                "status":
                    "in_transit",

                "current_location":
                    "Test Distribution Centre",

                "estimated_delivery":
                    "2026-10-16",

                "last_updated":
                    "2026-10-14T10:00:00",
            },

            "courier_status":
                "success",

            "courier_error":
                "",

            "answer":
                "Your order is in transit.",
        }


    monkeypatch.setattr(
        support_router_graph,
        "classify_intent",
        fake_classify_intent,
    )

    monkeypatch.setattr(
        support_router_graph,
        "run_shipment_workflow",
        fake_shipment_workflow,
    )


    result = (
        support_router_graph
        .run_support_request(
            order_number="ORD-TEST-1",

            question=
                "Where is my order?",
        )
    )


    assert result["intent"] == "WISMO"

    assert (
        result["status"]
        == "completed"
    )

    assert (
        result["courier_status"]
        == "success"
    )

    assert (
        result["shipment"]
        ["tracking_number"]
        == "TEST-TRACK-001"
    )

    assert (
        result["answer"]
        == "Your order is in transit."
    )


def test_return_route_pending_review(
    monkeypatch,
):

    def fake_classify_intent(
        question: str,
    ) -> str:

        return "RETURN"


    class FakeInterrupt:

        def __init__(self):

            self.value = {
                "draft_answer":
                    (
                        "This return requires "
                        "human approval."
                    ),

                "validation_issues": [
                    "Low retrieval confidence"
                ],

                "sources": [
                    {
                        "number": 1,
                        "source":
                            "uk_returns.md",
                        "heading":
                            "Standard Return Window",
                        "region":
                            "UK",
                        "score":
                            0.65,
                    }
                ],
            }


    def fake_return_workflow(
        order_number: str,
        question: str,
        thread_id: str,
    ) -> dict:

        return {
            "__interrupt__": [
                FakeInterrupt()
            ],

            "decision": {
                "order_number":
                    order_number,

                "days_since_delivery":
                    10,

                "eligible":
                    False,

                "reason":
                    "Test review reason",
            },
        }


    monkeypatch.setattr(
        support_router_graph,
        "classify_intent",
        fake_classify_intent,
    )

    monkeypatch.setattr(
        support_router_graph,
        "start_order_return_workflow",
        fake_return_workflow,
    )


    result = (
        support_router_graph
        .run_support_request(
            order_number="ORD-TEST-2",

            question=
                "Can I return this?",
        )
    )


    assert result["intent"] == "RETURN"

    assert (
        result["status"]
        == "pending_review"
    )

    assert (
        result["human_approved"]
        is None
    )

    assert (
        result["draft_answer"]
        == (
            "This return requires "
            "human approval."
        )
    )

    assert result[
        "validation_issues"
    ] == [
        "Low retrieval confidence"
    ]


def test_return_route_completed(
    monkeypatch,
):

    def fake_classify_intent(
        question: str,
    ) -> str:

        return "RETURN"


    def fake_return_workflow(
        order_number: str,
        question: str,
        thread_id: str,
    ) -> dict:

        return {
            "answer":
                (
                    "Your return is "
                    "eligible."
                ),

            "decision": {
                "order_number":
                    order_number,

                "days_since_delivery":
                    5,

                "eligible":
                    True,

                "reason":
                    (
                        "Return meets "
                        "policy requirements"
                    ),
            },

            "validation_issues":
                [],

            "human_approved":
                None,

            "sources":
                [],
        }


    monkeypatch.setattr(
        support_router_graph,
        "classify_intent",
        fake_classify_intent,
    )

    monkeypatch.setattr(
        support_router_graph,
        "start_order_return_workflow",
        fake_return_workflow,
    )


    result = (
        support_router_graph
        .run_support_request(
            order_number="ORD-TEST-3",

            question=
                "Can I return this?",
        )
    )


    assert result["intent"] == "RETURN"

    assert (
        result["status"]
        == "completed"
    )

    assert (
        result["answer"]
        == "Your return is eligible."
    )

    assert (
        result["decision"]
        ["eligible"]
        is True
    )


def test_unknown_route(
    monkeypatch,
):

    def fake_classify_intent(
        question: str,
    ) -> str:

        return "UNKNOWN"


    monkeypatch.setattr(
        support_router_graph,
        "classify_intent",
        fake_classify_intent,
    )


    result = (
        support_router_graph
        .run_support_request(
            order_number="ORD-TEST-4",

            question=(
                "Can you recommend "
                "a shirt?"
            ),
        )
    )


    assert (
        result["intent"]
        == "UNKNOWN"
    )

    assert (
        result["status"]
        == "completed"
    )

    assert (
        "return eligibility"
        in result["answer"]
    )

    assert (
        "shipment tracking"
        in result["answer"]
    )