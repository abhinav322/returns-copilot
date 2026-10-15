from pathlib import Path

from sentence_transformers import (
    CrossEncoder,
)

from backend.rag.pgvector_search import (
    search_policy_chunks,
)


MODEL_NAME = (
    "cross-encoder/"
    "ms-marco-MiniLM-L-6-v2"
)

MODEL_CACHE = Path(
    "data/models"
)


print(
    "Loading cross-encoder reranker..."
)


RERANKER = CrossEncoder(
    MODEL_NAME,
    cache_folder=str(
        MODEL_CACHE
    ),
)


def rerank_policy_chunks(
    query: str,
    top_k: int = 3,
    candidate_k: int = 6,
    region: str | None = None,
) -> list[dict]:

    candidates = (
        search_policy_chunks(
            query=query,
            top_k=candidate_k,
            region=region,
        )
    )


    if not candidates:

        return []


    pairs = []


    for candidate in candidates:

        document_text = (
            f"{candidate['heading']}\n"
            f"{candidate['text']}"
        )

        pairs.append(
            (
                query,
                document_text,
            )
        )


    reranker_scores = (
        RERANKER.predict(
            pairs
        )
    )


    reranked_results = []


    for (
        candidate,
        reranker_score,
    ) in zip(
        candidates,
        reranker_scores,
    ):

        result = {
            **candidate,

            "semantic_score":
                candidate["score"],

            "reranker_score":
                float(
                    reranker_score
                ),
        }

        reranked_results.append(
            result
        )


    reranked_results.sort(
        key=lambda result:
            result["reranker_score"],
        reverse=True,
    )


    return reranked_results[
        :top_k
    ]