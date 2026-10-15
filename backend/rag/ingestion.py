from pathlib import Path

from backend.rag.chunking import (
    load_markdown_file,
    split_by_headings,
)


POLICY_FOLDER = Path("data/policies")


DOCUMENT_METADATA = {
    "uk_returns.md": {
        "region": "UK",
        "document_type": "returns_policy",
        "policy_version": "2026-09",
    },
    "eu_returns.md": {
        "region": "EU",
        "document_type": "returns_policy",
        "policy_version": "2026-09",
    },
    "product_care.md": {
        "region": "ALL",
        "document_type": "product_care",
        "policy_version": "2026-09",
    },
}


def build_policy_chunks() -> list[dict]:
    all_chunks = []

    for file_path in POLICY_FOLDER.glob("*.md"):

        text = load_markdown_file(file_path)

        document_chunks = split_by_headings(text)

        metadata = DOCUMENT_METADATA[
            file_path.name
        ]

        for index, chunk in enumerate(
            document_chunks,
            start=1
        ):
            chunk_id = (
                f"{file_path.stem}_{index}"
            )

            all_chunks.append(
                {
                    "id": chunk_id,
                    "source": file_path.name,
                    "heading": chunk["heading"],
                    "text": chunk["text"],
                    "region": metadata["region"],
                    "document_type":
                        metadata["document_type"],
                    "policy_version":
                        metadata["policy_version"],
                }
            )

    return all_chunks