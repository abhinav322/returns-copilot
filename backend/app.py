from time import perf_counter
from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from sqlalchemy.orm import Session

from backend.config import (
    FRONTEND_ORIGIN,
)

from backend.database import (
    get_db,
)

from backend.logging_config import (
    logger,
)

from backend.models import (
    AssistantAnswerResponse,
    AssistantQuestionRequest,
    OrderResponse,
    OrderReturnWorkflowResponse,
    OrderReturnWorkflowReviewRequest,
    OrderReturnWorkflowStartRequest,
    ReturnCheckRequest,
    ReturnResponse,
    SupportRequest,
    SupportResponse,
)

from backend.repositories import (
    get_order_by_number,
)

from backend.services import (
    evaluate_return_for_order,
)

from backend.rag.rag_pipeline import (
    answer_question,
)

from backend.workflow.order_return_graph import (
    resume_order_return_workflow,
    start_order_return_workflow,
)

from backend.workflow.support_router_graph import (
    run_support_request,
)


app = FastAPI(
    title="Returns Copilot API",
    version="0.8.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_ORIGIN,
    ],
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Request-ID",
    ],
    expose_headers=[
        "X-Request-ID",
    ],
)


INVALID_REVIEW_MESSAGE = (
    "Could not resume the workflow. "
    "Check that the thread ID belongs "
    "to a currently paused workflow."
)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):

    request_id = (
        request.headers.get(
            "X-Request-ID"
        )
        or str(
            uuid4()
        )
    )

    request.state.request_id = (
        request_id
    )

    start_time = perf_counter()

    logger.info(
        "request_started",
        extra={
            "request_id":
                request_id,
            "method":
                request.method,
            "path":
                request.url.path,
        },
    )

    try:

        response = await call_next(
            request
        )

    except Exception:

        duration_ms = (
            perf_counter()
            - start_time
        ) * 1000

        logger.exception(
            "request_failed",
            extra={
                "request_id":
                    request_id,
                "method":
                    request.method,
                "path":
                    request.url.path,
                "duration_ms":
                    round(
                        duration_ms,
                        2,
                    ),
            },
        )

        raise

    duration_ms = (
        perf_counter()
        - start_time
    ) * 1000

    response.headers[
        "X-Request-ID"
    ] = request_id

    logger.info(
        "request_completed",
        extra={
            "request_id":
                request_id,
            "method":
                request.method,
            "path":
                request.url.path,
            "status_code":
                response.status_code,
            "duration_ms":
                round(
                    duration_ms,
                    2,
                ),
        },
    )

    return response


@app.get("/health")
def health_check():

    return {
        "status": "ok"
    }


@app.get(
    "/orders/{order_number}",
    response_model=OrderResponse,
)
def get_order(
    order_number: str,
    db: Session = Depends(get_db),
):

    order = get_order_by_number(
        db,
        order_number,
    )

    if order is None:

        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


@app.post(
    "/returns/check",
    response_model=ReturnResponse,
)
def check_return(
    request: ReturnCheckRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):

    result = (
        evaluate_return_for_order(
            db=db,
            order_number=
                request.order_number,
        )
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    logger.info(
        "return_eligibility_checked",
        extra={
            "request_id":
                http_request.state.request_id,
            "order_number":
                request.order_number,
        },
    )

    return result


@app.post(
    "/assistant/ask",
    response_model=AssistantAnswerResponse,
)
def ask_assistant(
    request: AssistantQuestionRequest,
    http_request: Request,
):

    result = answer_question(
        question=request.question,
        region=request.region,
        top_k=3,
    )

    logger.info(
        "rag_question_answered",
        extra={
            "request_id":
                http_request.state.request_id,
            "region":
                request.region,
            "source_count":
                len(
                    result.get(
                        "sources",
                        [],
                    )
                ),
        },
    )

    return result


@app.post(
    "/assistant/order-return/start",
    response_model=OrderReturnWorkflowResponse,
)
def start_order_return(
    request:
        OrderReturnWorkflowStartRequest,
    http_request: Request,
):

    thread_id = str(
        uuid4()
    )

    logger.info(
        "return_workflow_started",
        extra={
            "request_id":
                http_request.state.request_id,
            "thread_id":
                thread_id,
            "order_number":
                request.order_number,
        },
    )

    try:

        result = (
            start_order_return_workflow(
                order_number=
                    request.order_number,
                question=
                    request.question,
                thread_id=
                    thread_id,
            )
        )

    except ValueError:

        logger.warning(
            "return_workflow_order_not_found",
            extra={
                "request_id":
                    http_request.state.request_id,
                "thread_id":
                    thread_id,
                "order_number":
                    request.order_number,
            },
        )

        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    if "__interrupt__" in result:

        interrupt_data = (
            result[
                "__interrupt__"
            ][0].value
        )

        logger.info(
            "human_review_required",
            extra={
                "request_id":
                    http_request.state.request_id,
                "thread_id":
                    thread_id,
                "order_number":
                    request.order_number,
                "workflow_status":
                    "pending_review",
                "source_count":
                    len(
                        interrupt_data.get(
                            "sources",
                            [],
                        )
                    ),
            },
        )

        return {
            "status":
                "pending_review",
            "thread_id":
                thread_id,
            "answer":
                None,
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

    logger.info(
        "return_workflow_completed",
        extra={
            "request_id":
                http_request.state.request_id,
            "thread_id":
                thread_id,
            "order_number":
                request.order_number,
            "workflow_status":
                "completed",
            "source_count":
                len(
                    result.get(
                        "sources",
                        [],
                    )
                ),
        },
    )

    return {
        "status":
            "completed",
        "thread_id":
            thread_id,
        "answer":
            result.get(
                "answer"
            ),
        "draft_answer":
            None,
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


@app.post(
    "/assistant/order-return/review",
    response_model=OrderReturnWorkflowResponse,
)
def review_order_return(
    request:
        OrderReturnWorkflowReviewRequest,
    http_request: Request,
):

    try:

        result = (
            resume_order_return_workflow(
                thread_id=
                    request.thread_id,
                approved=
                    request.approved,
                edited_answer=
                    request.edited_answer,
            )
        )

    except Exception:

        logger.exception(
            "return_workflow_resume_failed",
            extra={
                "request_id":
                    http_request.state.request_id,
                "thread_id":
                    request.thread_id,
            },
        )

        raise HTTPException(
            status_code=400,
            detail=
                INVALID_REVIEW_MESSAGE,
        )

    if result.get(
        "human_approved"
    ) is False:

        status = "rejected"

    else:

        status = "completed"

    logger.info(
        "return_workflow_reviewed",
        extra={
            "request_id":
                http_request.state.request_id,
            "thread_id":
                request.thread_id,
            "workflow_status":
                status,
        },
    )

    return {
        "status":
            status,
        "thread_id":
            request.thread_id,
        "answer":
            result.get(
                "answer"
            ),
        "draft_answer":
            None,
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


@app.post(
    "/assistant/support",
    response_model=SupportResponse,
)
def support_assistant(
    request: SupportRequest,
    http_request: Request,
):

    try:

        result = run_support_request(
            order_number=
                request.order_number,
            question=
                request.question,
        )

    except ValueError:

        logger.warning(
            "support_request_failed",
            extra={
                "request_id":
                    http_request.state.request_id,
                "order_number":
                    request.order_number,
            },
        )

        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    logger.info(
        "support_request_routed",
        extra={
            "request_id":
                http_request.state.request_id,
            "thread_id":
                result["thread_id"],
            "order_number":
                request.order_number,
            "intent":
                result["intent"],
            "workflow_status":
                result.get(
                    "status",
                    "completed",
                ),
            "source_count":
                len(
                    result.get(
                        "sources",
                        [],
                    )
                ),
        },
    )

    return {
        "status":
            result.get(
                "status",
                "completed",
            ),
        "thread_id":
            result["thread_id"],
        "intent":
            result["intent"],
        "answer":
            result.get(
                "answer"
            ),
        "draft_answer":
            result.get(
                "draft_answer"
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
        "shipment":
            result.get(
                "shipment"
            ),
        "courier_status":
            result.get(
                "courier_status"
            ),
        "courier_error":
            result.get(
                "courier_error"
            ),
    }


@app.post(
    "/assistant/support/review",
    response_model=SupportResponse,
)
def review_support_response(
    request:
        OrderReturnWorkflowReviewRequest,
    http_request: Request,
):

    try:

        result = (
            resume_order_return_workflow(
                thread_id=
                    request.thread_id,
                approved=
                    request.approved,
                edited_answer=
                    request.edited_answer,
            )
        )

    except Exception:

        logger.exception(
            "support_review_failed",
            extra={
                "request_id":
                    http_request.state.request_id,
                "thread_id":
                    request.thread_id,
            },
        )

        raise HTTPException(
            status_code=400,
            detail=
                INVALID_REVIEW_MESSAGE,
        )

    if result.get(
        "human_approved"
    ) is False:

        status = "rejected"

    else:

        status = "completed"

    logger.info(
        "support_review_completed",
        extra={
            "request_id":
                http_request.state.request_id,
            "thread_id":
                request.thread_id,
            "intent":
                "RETURN",
            "workflow_status":
                status,
        },
    )

    return {
        "status":
            status,
        "thread_id":
            request.thread_id,
        "intent":
            "RETURN",
        "answer":
            result.get(
                "answer"
            ),
        "draft_answer":
            None,
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
        "shipment":
            None,
        "courier_status":
            None,
        "courier_error":
            None,
    }