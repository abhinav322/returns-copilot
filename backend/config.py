import os

from dotenv import load_dotenv


load_dotenv()


RAG_RELEVANCE_THRESHOLD = float(
    os.getenv(
        "RAG_RELEVANCE_THRESHOLD",
        "0.50",
    )
)


HUMAN_REVIEW_THRESHOLD = float(
    os.getenv(
        "HUMAN_REVIEW_THRESHOLD",
        "0.70",
    )
)


FRONTEND_ORIGIN = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173",
).strip()