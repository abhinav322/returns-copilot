from fastapi.testclient import TestClient

import backend.app as app_module


client = TestClient(
    app_module.app
)


def test_support_wismo_response(
    monkeypatch,
):

    def fake_run_support_request(
        order_number: str,
        question: str,
    ) -> dict:

        return {
            "order_number":
                order_number,

            "question":
                question,

            "thread_id":
                "test-wismo-thread",

            "intent":
                "WISMO",

            "status":
                "completed",

            "answer":
                (
                    "Your order is "
                    "currently in transit."
                ),

            "shipment": {
                "order_number":
                    order_number,

                "tracking_number":
                    "TEST-TRACK-001",

                "status":
                    "in_transit",

                "current_location":
                    "Test Depot",

                "estimated_delivery":
                    "2026-10-16",

                "last_updated":
                    "2026-10-14T10:00:00",
            },

            "courier_status":
                "success",

            "courier_error":
                "",
        }


    monkeypatch.setattr(
        app_module,
        "run_support_request",
        fake_run_support_request,
    )


    response = client.post(
        "/assistant/support",
        json={
            "order_number":
                "ORD-2001",

            "question":
                "Where is my order?",
        },
    )


    assert response.status_code == 200


    data = response.json()


    assert data["intent"] == "WISMO"

    assert (
        data["status"]
        == "completed"
    )

    assert (
        data["thread_id"]
        == "test-wismo-thread"
    )

    assert (
        data["courier_status"]
        == "success"
    )

    assert (
        data["shipment"]
        ["tracking_number"]
        == "TEST-TRACK-001"
    )


def test_support_return_pending_review(
    monkeypatch,
):

    def fake_run_support_request(
        order_number: str,
        question: str,
    ) -> dict:

        return {
            "order_number":
                order_number,

            "question":
                question,

            "thread_id":
                "test-return-thread",

            "intent":
                "RETURN",

            "status":
                "pending_review",

            "draft_answer":
                (
                    "This return requires "
                    "human review."
                ),

            "decision": {
                "order_number":
                    order_number,

                "days_since_delivery":
                    26,

                "eligible":
                    False,

                "reason":
                    "Item must be unused",
            },

            "validation_issues": [
                (
                    "Best retrieval score "
                    "is below threshold."
                )
            ],

            "human_approved":
                None,

            "sources": [
                {
                    "number": 1,

                    "source":
                        "product_care.md",

                    "heading":
                        "Returned Products",

                    "region":
                        "ALL",

                    "score":
                        0.69,
                }
            ],
        }


    monkeypatch.setattr(
        app_module,
        "run_support_request",
        fake_run_support_request,
    )


    response = client.post(
        "/assistant/support",
        json={
            "order_number":
                "ORD-1004",

            "question":
                "Can I return this order?",
        },
    )


    assert response.status_code == 200


    data = response.json()


    assert data["intent"] == "RETURN"

    assert (
        data["status"]
        == "pending_review"
    )

    assert (
        data["thread_id"]
        == "test-return-thread"
    )

    assert (
        data["answer"]
        is None
    )

    assert (
        data["draft_answer"]
        == (
            "This return requires "
            "human review."
        )
    )

    assert (
        data["decision"]
        ["eligible"]
        is False
    )

    assert (
        data["human_approved"]
        is None
    )


def test_support_unknown_response(
    monkeypatch,
):

    def fake_run_support_request(
        order_number: str,
        question: str,
    ) -> dict:

        return {
            "order_number":
                order_number,

            "question":
                question,

            "thread_id":
                "test-unknown-thread",

            "intent":
                "UNKNOWN",

            "status":
                "completed",

            "answer":
                (
                    "I can currently help "
                    "with returns and "
                    "shipment tracking."
                ),
        }


    monkeypatch.setattr(
        app_module,
        "run_support_request",
        fake_run_support_request,
    )


    response = client.post(
        "/assistant/support",
        json={
            "order_number":
                "ORD-1004",

            "question":
                "Recommend a shirt for me.",
        },
    )


    assert response.status_code == 200


    data = response.json()


    assert (
        data["intent"]
        == "UNKNOWN"
    )

    assert (
        data["status"]
        == "completed"
    )

    assert data["answer"] is not None

    assert data["shipment"] is None

    assert (
        data["decision"]
        is None
    )


def test_support_review_approved(
    monkeypatch,
):

    def fake_resume_workflow(
        thread_id: str,
        approved: bool,
        edited_answer: str | None = None,
    ) -> dict:

        assert (
            thread_id
            == "test-return-thread"
        )

        assert approved is True

        assert edited_answer is None


        return {
            "answer":
                (
                    "The return cannot "
                    "be accepted because "
                    "the item was used."
                ),

            "decision": {
                "order_number":
                    "ORD-1004",

                "days_since_delivery":
                    26,

                "eligible":
                    False,

                "reason":
                    "Item must be unused",
            },

            "validation_issues": [
                (
                    "Best retrieval score "
                    "is below threshold."
                )
            ],

            "human_approved":
                True,

            "sources": [
                {
                    "number": 1,

                    "source":
                        "product_care.md",

                    "heading":
                        "Returned Products",

                    "region":
                        "ALL",

                    "score":
                        0.69,
                }
            ],
        }


    monkeypatch.setattr(
        app_module,
        "resume_order_return_workflow",
        fake_resume_workflow,
    )


    response = client.post(
        "/assistant/support/review",
        json={
            "thread_id":
                "test-return-thread",

            "approved":
                True,

            "edited_answer":
                None,
        },
    )


    assert response.status_code == 200


    data = response.json()


    assert data["intent"] == "RETURN"

    assert (
        data["status"]
        == "completed"
    )

    assert (
        data["human_approved"]
        is True
    )

    assert (
        data["thread_id"]
        == "test-return-thread"
    )

    assert data["answer"] is not None


def test_support_request_validation():

    response = client.post(
        "/assistant/support",
        json={
            "order_number": "",
            "question": "Hi",
        },
    )


    assert response.status_code == 422