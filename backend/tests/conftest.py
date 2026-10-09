"""Shared test fixtures.

Every test gets its own temporary SQLite file, so tests never touch
backend/data/tracker.db and never affect each other.
"""

import os

# Fixed settings for tests, set before the app is imported.
# Real env vars win over the .env file, so the owner's .env can't change test results.
os.environ["LEETCODE_USERNAME"] = "testuser"
os.environ["TZ"] = "America/Toronto"
os.environ["DAILY_GOAL"] = "1"
os.environ["DATABASE_URL"] = "sqlite://"  # placeholder; replaced per test below

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, create_engine  # noqa: E402

import db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
def engine(tmp_path, monkeypatch):
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    # db.get_session and db.create_db_and_tables read db.engine, so swapping it is enough.
    monkeypatch.setattr(db, "engine", test_engine)
    db.create_db_and_tables()
    return test_engine


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(engine):
    with TestClient(app) as c:
        yield c
