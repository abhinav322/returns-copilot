import numpy as np

from backend.rag.embeddings import (
    embed_query,
    embed_texts,
)
from backend.rag.ingestion import (
    build_policy_chunks,
)


def search(
    query: str,
    top_k: int = 3
) -> list[dict]:

    chunks = build_policy_chunks()

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    chunk_embeddings = embed_texts(texts)

    query_embedding = embed_query(query)

    scores = np.dot(
        chunk_embeddings,
        query_embedding
    )

    ranked_indexes = np.argsort(
        scores
    )[::-1]

    results = []

    for index in ranked_indexes[:top_k]:

        chunk = chunks[index].copy()

        chunk["score"] = float(
            scores[index]
        )

        results.append(chunk)

    return results