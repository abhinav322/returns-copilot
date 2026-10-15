from sqlalchemy import select

from backend.rag.embeddings import (
    embed_query,
)

from backend.rag.vector_database import (
    VectorSessionLocal,
)

from backend.rag.vector_models import (
    PolicyChunk,
)


def search_policy_chunks(
    query: str,
    top_k: int = 3,
    region: str | None = None,
) -> list[dict]:

    query_embedding = embed_query(
        query
    ).tolist()

    distance = (
        PolicyChunk.embedding
        .cosine_distance(
            query_embedding
        )
        .label("distance")
    )

    statement = select(
        PolicyChunk,
        distance
    )

    if region is not None:

        statement = statement.where(
            PolicyChunk.region.in_(
                [region, "ALL"]
            )
        )

    statement = (
        statement
        .order_by(distance)
        .limit(top_k)
    )

    db = VectorSessionLocal()

    try:
        rows = db.execute(
            statement
        ).all()

        results = []

        for chunk, distance_value in rows:

            similarity = (
                1.0 - float(
                    distance_value
                )
            )

            results.append(
                {
                    "id": chunk.id,
                    "source": chunk.source,
                    "heading": chunk.heading,
                    "text": chunk.text,
                    "region": chunk.region,
                    "score": similarity,
                }
            )

        return results

    finally:
        db.close()