from pgvector.sqlalchemy import Vector

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.rag.vector_database import (
    VectorBase,
)


class PolicyChunk(VectorBase):
    __tablename__ = "policy_chunks"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True
    )

    source: Mapped[str] = mapped_column(
        String(255)
    )

    heading: Mapped[str] = mapped_column(
        String(255)
    )

    text: Mapped[str] = mapped_column(
        Text
    )

    region: Mapped[str] = mapped_column(
        String(20),
        index=True
    )

    document_type: Mapped[str] = mapped_column(
        String(50)
    )

    policy_version: Mapped[str] = mapped_column(
        String(50)
    )

    embedding: Mapped[list] = mapped_column(
        Vector(384)
    )