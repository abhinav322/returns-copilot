from sqlalchemy.orm import Session

from backend.repositories import (
    get_order_by_number,
)

from backend.services import (
    evaluate_return_for_order,
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


def answer_order_return_question(
    db: Session,
    order_number: str,
    question: str,
    top_k: int = 3,
    min_score: float = 0.50,
) -> dict | None:

    order = get_order_by_number(
        db,
        order_number,
    )

    if order is None:
        return None

    decision = evaluate_return_for_order(
        db=db,
        order_number=order_number,
    )

    retrieval_query = build_retrieval_query(
        question=question,
        reason=decision["reason"],
    )

    results = search_policy_chunks(
        query=retrieval_query,
        top_k=top_k,
        region=order.region,
    )

    relevant_results = [
        result
        for result in results
        if result["score"] >= min_score
    ]

    if relevant_results:

        policy_context = build_context(
            relevant_results
        )

        evidence_instructions = """
Relevant policy evidence was retrieved.

Use the policy context to explain the
deterministic decision.

Cite supporting policy statements using
markers such as [Source 1] or [Source 2].

Only cite sources that appear in the
POLICY CONTEXT.
"""

    else:

        policy_context = (
            "No policy evidence passed the "
            "retrieval confidence threshold."
        )

        evidence_instructions = """
No sufficiently relevant policy evidence
was retrieved.

Explain the deterministic business-rule
decision using the supplied order facts.

Do NOT claim that the decision is supported
by retrieved policy evidence.

Do NOT use citation markers such as
[Source 1].
"""

    prompt = f"""
You are a customer support assistant.

Use ONLY the information provided below.

Important rules:
- The deterministic return decision was
  calculated by application business logic.
- Do not override or contradict that decision.
- Explain the result clearly to the customer.
- Do not invent missing information.
- Do not expose unnecessary personal data.
- Keep the answer concise.

{evidence_instructions}

ORDER FACTS:
Order number: {order.order_number}
Product: {order.product_name}
Delivered at: {order.delivered_at}
Item condition: {order.item_condition}
Final sale: {order.final_sale}
Region: {order.region}

DETERMINISTIC RETURN DECISION:
Eligible: {decision['eligible']}
Days since delivery:
{decision['days_since_delivery']}
Reason: {decision['reason']}

CUSTOMER QUESTION:
{question}

POLICY CONTEXT:
{policy_context}
"""

    answer = generate_response(
        prompt
    )

    sources = []

    for index, result in enumerate(
        relevant_results,
        start=1
    ):

        sources.append(
            {
                "number": index,
                "source": result["source"],
                "heading": result["heading"],
                "region": result["region"],
                "score": result["score"],
            }
        )

    return {
        "order_number": order.order_number,
        "eligible": decision["eligible"],
        "reason": decision["reason"],
        "days_since_delivery":
            decision["days_since_delivery"],
        "answer": answer,
        "sources": sources,
    }