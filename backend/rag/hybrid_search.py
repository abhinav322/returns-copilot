import re

from rank_bm25 import BM25Okapi

from backend.rag.pgvector_search import (
    search_policy_chunks,
)


RRF_K = 60


def tokenize(
    text: str,
) -> list[str]:

    return re.findall(
        r"\b[a-z0-9]+\b",
        text.lower(),
    )


def hybrid_search_policy_chunks(
    query: str,
    top_k: int = 3,
    region: str | None = None,
) -> list[dict]:

    # Our policy collection is currently tiny,
    # so requesting a large top_k gives us all
    # region-eligible chunks.
    #
    # Later, for a large production collection,
    # semantic and keyword indexes would retrieve
    # their own limited candidate sets.

    semantic_results = (
        search_policy_chunks(
            query=query,
            top_k=100,
            region=region,
        )
    )


    if not semantic_results:

        return []


    # -----------------------------------------
    # 1. SEMANTIC RANKING
    # -----------------------------------------

    semantic_rank = {}

    for rank, result in enumerate(
        semantic_results,
        start=1,
    ):

        key = (
            result["source"],
            result["heading"],
        )

        semantic_rank[key] = rank


    # -----------------------------------------
    # 2. BUILD BM25 CORPUS
    # -----------------------------------------

    corpus_tokens = []

    for result in semantic_results:

        searchable_text = (
            f"{result['heading']} "
            f"{result['heading']} "
            f"{result['text']}"
        )

        corpus_tokens.append(
            tokenize(
                searchable_text
            )
        )


    bm25 = BM25Okapi(
        corpus_tokens
    )


    query_tokens = tokenize(
        query
    )


    bm25_scores = (
        bm25.get_scores(
            query_tokens
        )
    )


    # -----------------------------------------
    # 3. BM25 RANKING
    # -----------------------------------------

    bm25_positions = sorted(
        range(
            len(semantic_results)
        ),
        key=lambda index:
            bm25_scores[index],
        reverse=True,
    )


    bm25_rank = {}

    for rank, index in enumerate(
        bm25_positions,
        start=1,
    ):

        result = (
            semantic_results[index]
        )

        key = (
            result["source"],
            result["heading"],
        )

        bm25_rank[key] = rank


    # -----------------------------------------
    # 4. RECIPROCAL RANK FUSION
    # -----------------------------------------

    hybrid_results = []


    for index, result in enumerate(
        semantic_results
    ):

        key = (
            result["source"],
            result["heading"],
        )

        semantic_position = (
            semantic_rank[key]
        )

        keyword_position = (
            bm25_rank[key]
        )


        semantic_rrf = (
            1
            / (
                RRF_K
                + semantic_position
            )
        )


        keyword_rrf = (
            1
            / (
                RRF_K
                + keyword_position
            )
        )


        hybrid_score = (
            semantic_rrf
            + keyword_rrf
        )


        hybrid_result = {
            **result,

            "semantic_score":
                result["score"],

            "semantic_rank":
                semantic_position,

            "bm25_score":
                float(
                    bm25_scores[index]
                ),

            "bm25_rank":
                keyword_position,

            "hybrid_score":
                hybrid_score,
        }


        hybrid_results.append(
            hybrid_result
        )


    # -----------------------------------------
    # 5. SORT BY FUSED SCORE
    # -----------------------------------------

    hybrid_results.sort(
        key=lambda result:
            result["hybrid_score"],
        reverse=True,
    )


    return hybrid_results[
        :top_k
    ]