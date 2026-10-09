"""Database engine and session helpers."""

from pathlib import Path
from typing import Annotated

from fastapi import Depends
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

from config import settings

# check_same_thread=False: FastAPI may use the connection from a different thread
# than the one that opened it. That is safe here because each request gets its own session.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """Create the SQLite file's folder (if needed) and all tables."""
    # Import the models so SQLModel knows which tables exist.
    import models.tables  # noqa: F401

    db_path = engine.url.database
    if db_path and db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    SQLModel.metadata.create_all(engine)
    logger.info("Database ready at {}", engine.url)


def get_session():
    """FastAPI dependency: one session per request, closed afterwards."""
    with Session(engine) as session:
        yield session


# Shorthand for route parameters: `session: SessionDep` gives the route a DB session.
SessionDep = Annotated[Session, Depends(get_session)]
