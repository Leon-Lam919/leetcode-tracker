"""Tests for the LeetCode client. HTTP is faked by the `fake_leetcode` fixture in conftest."""

from datetime import UTC, datetime

import httpx
import pytest

from services import leetcode_client
from services.leetcode_client import LeetCodeError
from tests.conftest import load_fixture


def ok(fixture_name: str) -> httpx.Response:
    return httpx.Response(200, json=load_fixture(fixture_name))


def test_recent_accepted_parses_string_timestamps():
    submissions = leetcode_client.get_recent_accepted("someone")

    assert len(submissions) == 4
    first = submissions[0]
    assert first.title_slug == "valid-parentheses"
    assert first.solved_at == datetime(2026, 10, 8, 15, 30, tzinfo=UTC)


def test_real_empty_response_shape_parses(fake_leetcode):
    # Saved from a real request for poke213 (no recent public accepted submissions).
    fake_leetcode.queue(ok("recent_ac_poke213_real.json"))
    assert leetcode_client.get_recent_accepted("poke213") == []


def test_unknown_user_raises(fake_leetcode):
    fake_leetcode.queue(ok("recent_ac_user_not_found.json"))
    with pytest.raises(LeetCodeError, match="user not found"):
        leetcode_client.get_recent_accepted("no-such-user-xyz")


def test_get_question():
    info = leetcode_client.get_question("two-sum")
    assert info.title == "Two Sum"
    assert info.difficulty == "Easy"
    assert info.topics == ["Array", "Hash Table"]


def test_unknown_question_raises():
    with pytest.raises(LeetCodeError, match="not found"):
        leetcode_client.get_question("not-a-real-problem")


def test_retries_once_then_raises(fake_leetcode):
    fake_leetcode.down = True
    with pytest.raises(LeetCodeError, match="could not reach LeetCode"):
        leetcode_client.get_question("two-sum")
    assert fake_leetcode.calls == ["question", "question"]  # first try + one retry


def test_retry_succeeds_after_one_failure(fake_leetcode):
    fake_leetcode.queue(httpx.Response(503))  # then the normal answer
    assert leetcode_client.get_question("two-sum").title == "Two Sum"
    assert len(fake_leetcode.calls) == 2


def test_timeout_is_treated_as_failure(fake_leetcode):
    fake_leetcode.queue(httpx.ConnectTimeout("too slow"), httpx.ConnectTimeout("too slow"))
    with pytest.raises(LeetCodeError, match="could not reach LeetCode"):
        leetcode_client.get_question("two-sum")


def test_graphql_errors_raise_without_retry(fake_leetcode):
    fake_leetcode.queue(httpx.Response(200, json={"errors": [{"message": "rate limited"}]}))
    with pytest.raises(LeetCodeError, match="rate limited"):
        leetcode_client.get_question("two-sum")
    assert len(fake_leetcode.calls) == 1


def test_sends_browser_like_headers(fake_leetcode):
    leetcode_client.get_question("two-sum")
    headers = fake_leetcode.last_request.headers
    assert headers["Referer"] == "https://leetcode.com"
    assert headers["Content-Type"] == "application/json"
    assert "Mozilla" in headers["User-Agent"]
