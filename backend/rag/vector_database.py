import os

from dotenv import load_dotenv

from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    sessionmaker,
)


load_dotenv()


VECTOR_DATABASE_URL = os.getenv(
    "VECTOR_DATABASE_URL"
)


SQL_ECHO = (
    os.getenv(
        "SQL_ECHO",
        "false",
    ).lower()
    == "true"
)


vector_engine = create_engine(
    VECTOR_DATABASE_URL,
    echo=SQL_ECHO,
    pool_pre_ping=True,
)


VectorSessionLocal = sessionmaker(
    bind=vector_engine,
)


class VectorBase(
    DeclarativeBase,
):
    pass