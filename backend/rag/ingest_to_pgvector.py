from sqlalchemy import select

from backend.rag.embeddings import (
    embed_texts,
)

from backend.rag.ingestion import (
    build_policy_chunks,
)

from backend.rag.vector_database import (
    VectorSessionLocal,
)

from backend.rag.vector_models import (
    PolicyChunk,
)


def ingest_policy_chunks():

    chunks = build_policy_chunks()

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print(
        f"Embedding {len(texts)} chunks..."
    )

    embeddings = embed_texts(texts)

    db = VectorSessionLocal()

    try:

        inserted = 0
        skipped = 0

        for chunk, embedding in zip(
            chunks,
            embeddings
        ):

            existing = db.scalar(
                select(PolicyChunk).where(
                    PolicyChunk.id
                    == chunk["id"]
                )
            )

            if existing:
                skipped += 1
                continue

            record = PolicyChunk(
                id=chunk["id"],
                source=chunk["source"],
                heading=chunk["heading"],
                text=chunk["text"],
                region=chunk["region"],
                document_type=
                    chunk["document_type"],
                policy_version=
                    chunk["policy_version"],
                embedding=embedding.tolist(),
            )

            db.add(record)

            inserted += 1

        db.commit()

        print(
            f"Inserted: {inserted}"
        )

        print(
            f"Skipped existing: {skipped}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    ingest_policy_chunks()