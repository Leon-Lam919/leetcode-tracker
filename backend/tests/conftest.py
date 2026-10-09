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
os.environ["ENABLE_SCHEDULER"] = "false"  # background jobs never run in tests
os.environ["CORS_ORIGINS"] = "http://localhost:5174"
os.environ["NTFY_TOPIC"] = ""  # no real notifications, whatever the owner's .env says

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
import respx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, create_engine  # noqa: E402

import db  # noqa: E402
from main import app  # noqa: E402
from services.leetcode_client import GRAPHQL_URL  # noqa: E402


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


FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


class FakeLeetCode:
    """A stand-in for LeetCode's GraphQL endpoint, served through respx.

    Tests change its attributes to control what "LeetCode" answers.
    """

    def __init__(self):
        self.recent_response = load_fixture("recent_ac.json")
        self.questions = {
            "two-sum": load_fixture("question_two_sum.json"),
            "valid-parentheses": load_fixture("question_valid_parentheses.json"),
            "add-two-numbers": load_fixture("question_add_two_numbers.json"),
        }
        self.down = False  # True = every request fails with HTTP 503
        self.calls = []  # operation names, in order, e.g. ["recentAc", "question"]
        self.last_request = None
        self.queued = []  # exact responses (or exceptions) to return first, in order

    def queue(self, *responses):
        """Answer the next requests with these, before falling back to normal behaviour."""
        self.queued.extend(responses)

    def handle(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        operation = "recentAc" if "recentAcSubmissionList" in body["query"] else "question"
        self.calls.append(operation)
        self.last_request = request

        if self.queued:
            next_response = self.queued.pop(0)
            if isinstance(next_response, Exception):
                raise next_response
            return next_response
        if self.down:
            return httpx.Response(503)
        if operation == "recentAc":
            return httpx.Response(200, json=self.recent_response)

        slug = body["variables"]["titleSlug"]
        unknown = {"data": {"question": None}}
        return httpx.Response(200, json=self.questions.get(slug, unknown))


@pytest.fixture(autouse=True)
def fake_leetcode():
    """Used by every test. Any request to a URL we didn't mock fails the test,
    so no test can reach the real network."""
    fake = FakeLeetCode()
    with respx.mock(assert_all_called=False) as router:
        router.post(GRAPHQL_URL).mock(side_effect=fake.handle)
        fake.router = router  # tests can add more fake routes, e.g. for ntfy
        yield fake
