from backend.config import (
    RAG_RELEVANCE_THRESHOLD,
)

from backend.rag.ollama_client import (
    generate_response,
)

from backend.rag.pgvector_search import (
    search_policy_chunks,
)


def build_context(
    results: list[dict],
) -> str:

    context_sections = []

    for index, result in enumerate(
        results,
        start=1,
    ):

        section = (
            f"[Source {index}]\n"
            f"Document: {result['source']}\n"
            f"Section: {result['heading']}\n"
            f"Region: {result['region']}\n"
            f"Content:\n{result['text']}"
        )

        context_sections.append(
            section
        )

    return "\n\n".join(
        context_sections
    )


def answer_question(
    question: str,
    region: str = "UK",
    top_k: int = 3,
    min_score: float | None = None,
) -> dict:

    if min_score is None:
        min_score = (
            RAG_RELEVANCE_THRESHOLD
        )

    results = search_policy_chunks(
        query=question,
        top_k=top_k,
        region=region,
    )

    relevant_results = [
        result
        for result in results
        if result["score"] >= min_score
    ]

    if not relevant_results:

        return {
            "answer": (
                "The available policy documents "
                "do not contain enough information "
                "to answer this question."
            ),
            "sources": [],
        }

    context = build_context(
        relevant_results
    )

    prompt = f"""
Answer the customer question using ONLY the
policy context provided below.

Rules:
- Do not use outside knowledge.
- Do not invent policy information.
- If the context does not contain enough
  information, say that the policy documents
  do not provide enough information.
- Keep the answer concise.
- Cite supporting evidence using markers such
  as [Source 1] or [Source 2].

CUSTOMER QUESTION:
{question}

POLICY CONTEXT:
{context}
"""

    answer = generate_response(
        prompt
    )

    sources = []

    for index, result in enumerate(
        relevant_results,
        start=1,
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
        "answer": answer,
        "sources": sources,
    }