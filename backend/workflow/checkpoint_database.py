import os

from dotenv import load_dotenv

from psycopg import connect
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres import (
    PostgresSaver,
)


load_dotenv()


CHECKPOINT_DATABASE_URL = os.getenv(
    "CHECKPOINT_DATABASE_URL"
)


if not CHECKPOINT_DATABASE_URL:
    raise RuntimeError(
        "CHECKPOINT_DATABASE_URL "
        "is not configured."
    )


checkpoint_connection = connect(
    CHECKPOINT_DATABASE_URL,
    autocommit=True,
    prepare_threshold=0,
    row_factory=dict_row,
)


CHECKPOINTER = PostgresSaver(
    checkpoint_connection
)