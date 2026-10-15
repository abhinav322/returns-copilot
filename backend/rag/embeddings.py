from sentence_transformers import (
    SentenceTransformer,
)


MODEL_NAME = "all-MiniLM-L6-v2"

MODEL_CACHE = "data/models"


model = SentenceTransformer(
    MODEL_NAME,
    cache_folder=MODEL_CACHE,
)


def embed_texts(
    texts: list[str]
):
    return model.encode(
        texts,
        normalize_embeddings=True,
    )


def embed_query(
    query: str
):
    return model.encode(
        query,
        normalize_embeddings=True,
    )