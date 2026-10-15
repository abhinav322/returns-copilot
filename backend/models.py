from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)


class ReturnCheckRequest(BaseModel):
    order_number: str = Field(
        min_length=1,
        description=(
            "Order number to check "
            "for return eligibility"
        ),
    )


class ReturnResponse(BaseModel):
    order_number: str
    eligible: bool
    reason: str
    days_since_delivery: int


class OrderResponse(BaseModel):
    order_number: str
    customer_email: str
    product_name: str
    delivered_at: date
    item_condition: str
    final_sale: bool
    region: str

    model_config = {
        "from_attributes": True
    }


class AssistantQuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        description=(
            "Customer question for "
            "the support assistant"
        ),
    )

    region: Literal[
        "UK",
        "EU",
    ] = "UK"


class AssistantSourceResponse(BaseModel):
    number: int
    source: str
    heading: str
    region: str
    score: float


class AssistantAnswerResponse(BaseModel):
    answer: str

    sources: list[
        AssistantSourceResponse
    ]


class OrderReturnWorkflowStartRequest(
    BaseModel
):
    order_number: str = Field(
        min_length=1,
        description="Customer order number",
    )

    question: str = Field(
        min_length=3,
        description=(
            "Customer question "
            "about the return"
        ),
    )


class OrderReturnWorkflowReviewRequest(
    BaseModel
):
    thread_id: str = Field(
        min_length=1,
        description=(
            "Workflow thread ID returned "
            "by the start endpoint"
        ),
    )

    approved: bool

    edited_answer: str | None = None


class OrderReturnWorkflowResponse(
    BaseModel
):
    status: Literal[
        "completed",
        "pending_review",
        "rejected",
    ]

    thread_id: str

    answer: str | None = None

    draft_answer: str | None = None

    decision: dict | None = None

    validation_issues: list[str] = Field(
        default_factory=list
    )

    human_approved: bool | None = None

    sources: list[
        AssistantSourceResponse
    ] = Field(
        default_factory=list
    )


class SupportRequest(BaseModel):

    order_number: str = Field(
        min_length=1,
        description=(
            "Customer order number"
        ),
    )

    question: str = Field(
        min_length=3,
        description=(
            "Customer support question"
        ),
    )


class SupportResponse(BaseModel):

    status: Literal[
        "completed",
        "pending_review",
        "rejected",
    ]

    thread_id: str

    intent: Literal[
        "RETURN",
        "WISMO",
        "UNKNOWN",
    ]

    answer: str | None = None

    draft_answer: str | None = None

    decision: dict | None = None

    validation_issues: list[str] = Field(
        default_factory=list
    )

    human_approved: bool | None = None

    sources: list[
        AssistantSourceResponse
    ] = Field(
        default_factory=list
    )

    shipment: dict | None = None

    courier_status: str | None = None

    courier_error: str | None = None