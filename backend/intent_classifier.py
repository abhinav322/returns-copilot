from backend.rag.ollama_client import (
    generate_response,
)


VALID_INTENTS = {
    "RETURN",
    "WISMO",
    "UNKNOWN",
}


def classify_intent(
    question: str,
) -> str:

    prompt = f"""
You are an intent classifier for an
e-commerce customer support system.

Classify the customer's question into
exactly ONE of these categories:

RETURN
- return eligibility
- returns
- exchanges
- refund eligibility
- item condition for returns

WISMO
- where is my order
- shipment tracking
- delivery status
- delayed shipment
- estimated delivery

UNKNOWN
- anything that does not clearly belong
  to RETURN or WISMO

Important rules:
- Output ONLY one word.
- The only valid outputs are:
  RETURN
  WISMO
  UNKNOWN
- Do not explain your answer.

CUSTOMER QUESTION:
{question}
"""

    raw_response = generate_response(
        prompt
    )

    cleaned_response = (
        raw_response
        .strip()
        .upper()
        .replace(".", "")
    )

    if cleaned_response in VALID_INTENTS:

        return cleaned_response


    # Defensive fallback in case the LLM
    # ignores our output instructions.

    question_lower = (
        question.lower()
    )


    return_keywords = [
        "return",
        "refund",
        "exchange",
    ]

    wismo_keywords = [
        "where is my order",
        "track",
        "tracking",
        "shipment",
        "delivery",
        "delayed",
    ]


    if any(
        keyword in question_lower
        for keyword in return_keywords
    ):

        return "RETURN"


    if any(
        keyword in question_lower
        for keyword in wismo_keywords
    ):

        return "WISMO"


    return "UNKNOWN"