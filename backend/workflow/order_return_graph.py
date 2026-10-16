import re

from datetime import date

from typing import (
    Literal,
    TypedDict,
)

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from langgraph.types import (
    Command,
    interrupt,
)

from backend.config import (
    HUMAN_REVIEW_THRESHOLD,
    RAG_RELEVANCE_THRESHOLD,
)

from backend.database import (
    SessionLocal,
)

from backend.repositories import (
    get_order_by_number,
)

from backend.returns_logic import (
    check_return_eligibility,
)

from backend.rag.ollama_client import (
    generate_response,
)

from backend.rag.pgvector_search import (
    search_policy_chunks,
)

from backend.rag.rag_pipeline import (
    build_context,
)

from backend.workflow.checkpoint_database import (
    CHECKPOINTER,
)


class OrderReturnState(
    TypedDict,
    total=False,
):
    order_number: str
    question: str

    order: dict
    decision: dict

    retrieval_query: str

    retrieved_results: list[dict]
    relevant_results: list[dict]

    policy_context: str

    answer: str
    sources: list[dict]

    validation_issues: list[str]

    needs_human_review: bool
    human_approved: bool


def matches_any_pattern(
    text: str,
    patterns: list[str],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        is not None

        for pattern in patterns
    )


def matches_asserted_pattern(
    text: str,
    patterns: list[str],
) -> bool:
    """
    Return True only when a pattern appears as
    an asserted statement rather than inside a
    conditional phrase such as:

    - whether it is ...
    - whether the item is ...
    - whether or not it is ...
    - if it is ...

    This prevents the validator from treating
    discussion of a possible order property as
    a factual claim about the order.
    """

    conditional_prefix = (
        r"\b(?:"
        r"whether"
        r"(?:\s+or\s+not)?"
        r"|if"
        r")\s*$"
    )

    for pattern in patterns:

        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):

            prefix = text[
                :match.start()
            ]

            if re.search(
                conditional_prefix,
                prefix,
                flags=re.IGNORECASE,
            ):
                continue

            return True

    return False


def claims_order_is_final_sale(
    text: str,
) -> bool:
    patterns = [
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|order|product)\s+"
            r"(?:is|was)\s+"
            r"marked\s+as\s+"
            r"(?:a\s+)?final\s+sale\b"
        ),
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|order|product)\s+"
            r"(?:is|was)\s+"
            r"(?:a\s+)?final\s+sale\b"
        ),
        (
            r"\bit\s+"
            r"(?:is|was)\s+"
            r"marked\s+as\s+"
            r"(?:a\s+)?final\s+sale\b"
        ),
    ]

    return matches_asserted_pattern(
        text,
        patterns,
    )


def claims_order_is_not_final_sale(
    text: str,
) -> bool:
    patterns = [
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|order|product)\s+"
            r"(?:is|was)\s+not\s+"
            r"(?:marked\s+as\s+)?"
            r"(?:a\s+)?final\s+sale\b"
        ),
        (
            r"\bit\s+"
            r"(?:is|was)\s+not\s+"
            r"marked\s+as\s+"
            r"(?:a\s+)?final\s+sale\b"
        ),
    ]

    return matches_asserted_pattern(
        text,
        patterns,
    )


def claims_item_is_used(
    text: str,
) -> bool:
    patterns = [
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|product)\s+"
            r"(?:is|was|has\s+been)\s+"
            r"(?:used|worn)\b"
        ),
        (
            r"\bit\s+"
            r"(?:is|was|has\s+been)\s+"
            r"(?:used|worn)\b"
        ),
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|product)\s+"
            r"(?:shows|showed)\s+"
            r"signs\s+of\s+wear\b"
        ),
    ]

    return matches_any_pattern(
        text,
        patterns,
    )


def claims_item_is_unused(
    text: str,
) -> bool:
    patterns = [
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|product)\s+"
            r"(?:is|was)\s+unused\b"
        ),
        (
            r"\bit\s+"
            r"(?:is|was)\s+unused\b"
        ),
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|product)\s+"
            r"(?:is|was)\s+unworn\b"
        ),
    ]

    return matches_any_pattern(
        text,
        patterns,
    )


def claims_order_is_eligible(
    text: str,
) -> bool:
    patterns = [
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|order|product|return)\s+"
            r"(?:is|was)\s+eligible\b"
        ),
        (
            r"\byou\s+can\s+return\s+"
            r"(?:this|the|your)\s+"
            r"(?:item|order|product)\b"
        ),
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|order|product)\s+"
            r"can\s+be\s+returned\b"
        ),
    ]

    return matches_any_pattern(
        text,
        patterns,
    )


def claims_order_is_ineligible(
    text: str,
) -> bool:
    patterns = [
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|order|product|return)\s+"
            r"(?:is|was)\s+not\s+eligible\b"
        ),
        (
            r"\b(?:this|the|your)\s+"
            r"(?:item|order|product)\s+"
            r"cannot\s+be\s+returned\b"
        ),
        (
            r"\byou\s+cannot\s+return\s+"
            r"(?:this|the|your)\s+"
            r"(?:item|order|product)\b"
        ),
        (
            r"\bthe\s+return\s+"
            r"is\s+not\s+eligible\b"
        ),
    ]

    return matches_any_pattern(
        text,
        patterns,
    )


def claims_within_return_window(
    text: str,
) -> bool:
    patterns = [
        r"\bwithin\s+(?:the\s+)?30[-\s]?day",
        r"\bwithin\s+(?:the\s+)?return\s+window\b",
        r"\bstill\s+within\s+(?:the\s+)?return\s+window\b",
    ]

    return matches_any_pattern(
        text,
        patterns,
    )


def claims_return_window_exceeded(
    text: str,
) -> bool:
    patterns = [
        r"\bmore\s+than\s+30\s+days\b",
        r"\bover\s+30\s+days\b",
        r"\breturn\s+window\s+(?:has\s+)?expired\b",
        r"\breturn\s+window\s+(?:has\s+)?been\s+exceeded\b",
        r"\breturn\s+window\s+(?:has\s+)?exceeded\b",
        r"\boutside\s+(?:the\s+)?30[-\s]?day\s+window\b",
    ]

    return matches_any_pattern(
        text,
        patterns,
    )


def incorrectly_attributes_decision_to_policy(
    text: str,
) -> bool:
    patterns = [
        (
            r"\b(?:decision|eligibility)\b"
            r".{0,120}"
            r"\bbased\s+on\b"
            r".{0,60}"
            r"\bpolicy\b"
        ),
        (
            r"\bpolicy\b"
            r".{0,80}"
            r"\b(?:determined|calculated)\b"
            r".{0,60}"
            r"\b(?:decision|eligibility)\b"
        ),
    ]

    return matches_any_pattern(
        text,
        patterns,
    )


def build_retrieval_query(
    question: str,
    reason: str,
) -> str:
    if reason == "Return window exceeded":
        return (
            f"{question} "
            "standard return window "
            "30 days from delivery "
            "return eligibility"
        )

    if reason == (
        "Final sale items cannot be returned"
    ):
        return (
            f"{question} "
            "final sale items "
            "return exchange restriction"
        )

    if reason == "Item must be unused":
        return (
            f"{question} "
            "returned products must be unused "
            "unworn original condition "
            "signs of wear washing alteration"
        )

    return (
        f"{question} "
        "return eligibility policy"
    )


def build_sources(
    results: list[dict],
) -> list[dict]:
    sources = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        sources.append(
            {
                "number":
                    index,

                "source":
                    result["source"],

                "heading":
                    result["heading"],

                "region":
                    result["region"],

                "score":
                    result["score"],
            }
        )

    return sources


def build_order_return_graph():

    def fetch_order(
        state: OrderReturnState,
    ) -> dict:
        db = SessionLocal()

        try:
            order = get_order_by_number(
                db,
                state["order_number"],
            )

            if order is None:
                raise ValueError(
                    "Order not found"
                )

            order_data = {
                "order_number":
                    order.order_number,

                "product_name":
                    order.product_name,

                "delivered_at":
                    order.delivered_at,

                "item_condition":
                    order.item_condition,

                "final_sale":
                    order.final_sale,

                "region":
                    order.region,
            }

            return {
                "order":
                    order_data
            }

        finally:
            db.close()


    def check_eligibility(
        state: OrderReturnState,
    ) -> dict:
        order = state[
            "order"
        ]

        current_date = date.today()

        days_since_delivery = (
            current_date
            - order["delivered_at"]
        ).days

        result = (
            check_return_eligibility(
                days_since_delivery=
                    days_since_delivery,

                item_condition=
                    order["item_condition"],

                final_sale=
                    order["final_sale"],
            )
        )

        decision = {
            "order_number":
                order["order_number"],

            "days_since_delivery":
                days_since_delivery,

            "eligible":
                result["eligible"],

            "reason":
                result["reason"],
        }

        return {
            "decision":
                decision
        }


    def retrieve_policy(
        state: OrderReturnState,
    ) -> dict:
        decision = state[
            "decision"
        ]

        order = state[
            "order"
        ]

        retrieval_query = (
            build_retrieval_query(
                question=
                    state["question"],

                reason=
                    decision["reason"],
            )
        )

        results = (
            search_policy_chunks(
                query=
                    retrieval_query,

                top_k=
                    3,

                region=
                    order["region"],
            )
        )

        relevant_results = [
            result

            for result in results

            if (
                result["score"]
                >= RAG_RELEVANCE_THRESHOLD
            )
        ]

        if relevant_results:
            policy_context = (
                build_context(
                    relevant_results
                )
            )

        else:
            policy_context = (
                "No sufficiently relevant "
                "policy evidence was retrieved."
            )

        return {
            "retrieval_query":
                retrieval_query,

            "retrieved_results":
                results,

            "relevant_results":
                relevant_results,

            "policy_context":
                policy_context,
        }


    def route_after_retrieval(
        state: OrderReturnState,
    ) -> Literal[
        "with_policy",
        "without_policy",
    ]:
        if state[
            "relevant_results"
        ]:
            return "with_policy"

        return "without_policy"


    def draft_with_policy(
        state: OrderReturnState,
    ) -> dict:
        order = state[
            "order"
        ]

        decision = state[
            "decision"
        ]

        prompt = f"""
You are a customer support assistant.

Use ONLY the information provided below.

Important rules:
- The deterministic return decision was
  calculated by application business logic.
- Never override or contradict that decision.
- Explain the decision clearly and concisely.
- Retrieved policy is supporting evidence only.
- Policy text describes general rules and does
  not establish facts about this specific order.
- Only ORDER FACTS establish whether this item
  is final sale, used, unused, or otherwise has
  a particular order-specific property.
- Do not infer an order fact merely because a
  related policy section was retrieved.
- Do not add a second order-specific reason
  unless it is supported by ORDER FACTS.
- Do not say that policy evidence calculated,
  determined, or produced the return decision.
- Do not invent information.
- Do not say "regardless of" unless that exact
  conclusion is explicitly supported.
- Cite only sources contained in POLICY CONTEXT.
- Use citation markers such as [Source 1].
- Do not claim anything stronger than the
  source text actually states.

ORDER FACTS:
Order number: {order['order_number']}
Product: {order['product_name']}
Delivered at: {order['delivered_at']}
Item condition: {order['item_condition']}
Final sale: {order['final_sale']}
Region: {order['region']}

DETERMINISTIC RETURN DECISION:
Eligible: {decision['eligible']}
Days since delivery:
{decision['days_since_delivery']}
Reason: {decision['reason']}

CUSTOMER QUESTION:
{state['question']}

POLICY CONTEXT:
{state['policy_context']}
"""

        answer = generate_response(
            prompt
        )

        sources = build_sources(
            state["relevant_results"]
        )

        return {
            "answer":
                answer,

            "sources":
                sources,
        }


    def draft_without_policy(
        state: OrderReturnState,
    ) -> dict:
        order = state[
            "order"
        ]

        decision = state[
            "decision"
        ]

        prompt = f"""
You are a customer support assistant.

Explain the deterministic return decision
using ONLY the order facts and decision below.

Important rules:
- Do not override the deterministic decision.
- Only ORDER FACTS establish facts about this
  specific order.
- Do not invent a final-sale, condition, or
  eligibility fact that is not shown below.
- Do not claim that policy evidence was
  retrieved.
- Do not use citation markers.
- Do not invent information.
- Keep the answer concise.

ORDER FACTS:
Order number: {order['order_number']}
Product: {order['product_name']}
Delivered at: {order['delivered_at']}
Item condition: {order['item_condition']}
Final sale: {order['final_sale']}
Region: {order['region']}

DETERMINISTIC RETURN DECISION:
Eligible: {decision['eligible']}
Days since delivery:
{decision['days_since_delivery']}
Reason: {decision['reason']}

CUSTOMER QUESTION:
{state['question']}
"""

        answer = generate_response(
            prompt
        )

        return {
            "answer":
                answer,

            "sources":
                [],
        }


    def validate_answer(
        state: OrderReturnState,
    ) -> dict:
        answer = state[
            "answer"
        ]

        sources = state.get(
            "sources",
            [],
        )

        decision = state[
            "decision"
        ]

        order = state[
            "order"
        ]

        issues = []

        answer_lower = (
            answer.lower()
        )


        citation_numbers = {
            int(number)

            for number in re.findall(
                r"\[Source\s+(\d+)\]",
                answer,
                flags=re.IGNORECASE,
            )
        }

        valid_source_numbers = {
            source["number"]
            for source in sources
        }

        invalid_citations = (
            citation_numbers
            - valid_source_numbers
        )


        if invalid_citations:
            issues.append(
                "The answer cites a source "
                "that was not actually retrieved."
            )


        if (
            sources
            and not citation_numbers
        ):
            issues.append(
                "Policy evidence was retrieved "
                "but the answer contains no "
                "source citation."
            )


        if (
            not sources
            and citation_numbers
        ):
            issues.append(
                "The answer contains citations "
                "even though no policy evidence "
                "was retrieved."
            )


        reason = decision[
            "reason"
        ]


        if reason == (
            "Return window exceeded"
        ):
            if not any(
                phrase in answer_lower

                for phrase in [
                    "30 day",
                    "30-day",
                    "return window",
                    "days since",
                ]
            ):
                issues.append(
                    "The answer does not clearly "
                    "explain the return-window "
                    "reason."
                )


        elif reason == (
            "Final sale items "
            "cannot be returned"
        ):
            if (
                "final sale"
                not in answer_lower
            ):
                issues.append(
                    "The answer does not clearly "
                    "explain the final-sale "
                    "reason."
                )


        elif reason == (
            "Item must be unused"
        ):
            if not any(
                phrase in answer_lower

                for phrase in [
                    "unused",
                    "used",
                    "wear",
                    "worn",
                ]
            ):
                issues.append(
                    "The answer does not clearly "
                    "explain the item-condition "
                    "reason."
                )


        if (
            decision["eligible"] is False
            and claims_order_is_eligible(
                answer_lower
            )
        ):
            issues.append(
                "The answer contradicts the "
                "deterministic decision by "
                "claiming that this order is "
                "eligible for return."
            )


        if (
            decision["eligible"] is True
            and claims_order_is_ineligible(
                answer_lower
            )
        ):
            issues.append(
                "The answer contradicts the "
                "deterministic decision by "
                "claiming that this order is "
                "not eligible for return."
            )


        if (
            order["final_sale"] is False
            and claims_order_is_final_sale(
                answer_lower
            )
        ):
            issues.append(
                "The answer incorrectly claims "
                "that this order is a final-sale "
                "item."
            )


        if (
            order["final_sale"] is True
            and claims_order_is_not_final_sale(
                answer_lower
            )
        ):
            issues.append(
                "The answer incorrectly claims "
                "that this order is not a "
                "final-sale item."
            )


        item_condition = str(
            order["item_condition"]
        ).strip().lower()


        if (
            item_condition == "unused"
            and claims_item_is_used(
                answer_lower
            )
        ):
            issues.append(
                "The answer incorrectly claims "
                "that this item is used or worn, "
                "but the order record says it "
                "is unused."
            )


        if (
            item_condition == "used"
            and claims_item_is_unused(
                answer_lower
            )
        ):
            issues.append(
                "The answer incorrectly claims "
                "that this item is unused, but "
                "the order record says it is "
                "used."
            )


        days_since_delivery = (
            decision[
                "days_since_delivery"
            ]
        )


        if (
            days_since_delivery > 30
            and claims_within_return_window(
                answer_lower
            )
        ):
            issues.append(
                "The answer incorrectly claims "
                "that the order is still within "
                "the return window."
            )


        if (
            days_since_delivery <= 30
            and claims_return_window_exceeded(
                answer_lower
            )
        ):
            issues.append(
                "The answer incorrectly claims "
                "that the return window has "
                "already been exceeded."
            )


        if (
            "regardless of"
            in answer_lower
        ):
            issues.append(
                "The answer contains an "
                "overly broad 'regardless of' "
                "claim."
            )


        if (
            "based solely on the policy"
            in answer_lower

            or

            "based solely on policy"
            in answer_lower
        ):
            issues.append(
                "The answer incorrectly implies "
                "that policy evidence calculated "
                "the deterministic decision."
            )


        if incorrectly_attributes_decision_to_policy(
            answer_lower
        ):
            issues.append(
                "The answer incorrectly implies "
                "that the deterministic return "
                "decision was based on policy "
                "retrieval rather than "
                "application business logic."
            )


        if not sources:
            issues.append(
                "No retrieved policy evidence "
                "is available to support the "
                "customer-facing explanation."
            )

        else:
            best_score = max(
                source["score"]
                for source in sources
            )

            if (
                best_score
                < HUMAN_REVIEW_THRESHOLD
            ):
                issues.append(
                    "Best retrieval score is "
                    f"{best_score:.4f}, below "
                    "the human-review threshold "
                    f"of "
                    f"{HUMAN_REVIEW_THRESHOLD:.2f}."
                )


        return {
            "validation_issues":
                issues,

            "needs_human_review":
                bool(issues),
        }


    def route_after_validation(
        state: OrderReturnState,
    ) -> Literal[
        "safe",
        "human_review",
    ]:
        if state[
            "needs_human_review"
        ]:
            return "human_review"

        return "safe"


    def human_review(
        state: OrderReturnState,
    ) -> dict:
        review = interrupt(
            {
                "question":
                    (
                        "Approve this drafted "
                        "customer response?"
                    ),

                "order_number":
                    state["order_number"],

                "draft_answer":
                    state["answer"],

                "validation_issues":
                    state[
                        "validation_issues"
                    ],

                "sources":
                    state["sources"],
            }
        )


        if isinstance(
            review,
            dict,
        ):
            approved = bool(
                review.get(
                    "approved",
                    False,
                )
            )

            edited_answer = (
                review.get(
                    "edited_answer"
                )
            )

        else:
            approved = bool(
                review
            )

            edited_answer = None


        if approved:
            if (
                isinstance(
                    edited_answer,
                    str,
                )

                and

                edited_answer.strip()
            ):
                final_answer = (
                    edited_answer.strip()
                )

            else:
                final_answer = (
                    state["answer"]
                )


            return {
                "answer":
                    final_answer,

                "human_approved":
                    True,

                "needs_human_review":
                    False,
            }


        return {
            "answer":
                (
                    "This response was not "
                    "approved by the human "
                    "reviewer."
                ),

            "human_approved":
                False,

            "needs_human_review":
                True,
        }


    builder = StateGraph(
        OrderReturnState
    )


    builder.add_node(
        "fetch_order",
        fetch_order,
    )

    builder.add_node(
        "check_eligibility",
        check_eligibility,
    )

    builder.add_node(
        "retrieve_policy",
        retrieve_policy,
    )

    builder.add_node(
        "draft_with_policy",
        draft_with_policy,
    )

    builder.add_node(
        "draft_without_policy",
        draft_without_policy,
    )

    builder.add_node(
        "validate_answer",
        validate_answer,
    )

    builder.add_node(
        "human_review",
        human_review,
    )


    builder.add_edge(
        START,
        "fetch_order",
    )

    builder.add_edge(
        "fetch_order",
        "check_eligibility",
    )

    builder.add_edge(
        "check_eligibility",
        "retrieve_policy",
    )


    builder.add_conditional_edges(
        "retrieve_policy",
        route_after_retrieval,
        {
            "with_policy":
                "draft_with_policy",

            "without_policy":
                "draft_without_policy",
        },
    )


    builder.add_edge(
        "draft_with_policy",
        "validate_answer",
    )

    builder.add_edge(
        "draft_without_policy",
        "validate_answer",
    )


    builder.add_conditional_edges(
        "validate_answer",
        route_after_validation,
        {
            "safe":
                END,

            "human_review":
                "human_review",
        },
    )


    builder.add_edge(
        "human_review",
        END,
    )


    return builder.compile(
        checkpointer=
            CHECKPOINTER
    )


ORDER_RETURN_GRAPH = (
    build_order_return_graph()
)


def start_order_return_workflow(
    order_number: str,
    question: str,
    thread_id: str,
) -> dict:
    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }

    initial_state = {
        "order_number":
            order_number,

        "question":
            question,
    }

    return ORDER_RETURN_GRAPH.invoke(
        initial_state,
        config=config,
    )


def resume_order_return_workflow(
    thread_id: str,
    approved: bool,
    edited_answer: str | None = None,
) -> dict:
    config = {
        "configurable": {
            "thread_id":
                thread_id
        }
    }

    resume_data = {
        "approved":
            approved,

        "edited_answer":
            edited_answer,
    }

    return ORDER_RETURN_GRAPH.invoke(
        Command(
            resume=
                resume_data
        ),
        config=config,
    )