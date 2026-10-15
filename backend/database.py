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


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


SQL_ECHO = (
    os.getenv(
        "SQL_ECHO",
        "false",
    ).lower()
    == "true"
)


engine = create_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
)


class Base(
    DeclarativeBase,
):
    pass


def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()