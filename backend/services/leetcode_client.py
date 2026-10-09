"""Every call to LeetCode lives in this one file.

LeetCode's GraphQL API is unofficial and can change without notice. Keeping all
of it here means a change on their side only needs a fix in one place.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from loguru import logger

GRAPHQL_URL = "https://leetcode.com/graphql"
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    # LeetCode rejects requests that don't look like they come from a browser.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
}
TIMEOUT_SECONDS = 10
ATTEMPTS = 2  # try once, retry once

RECENT_AC_QUERY = """
query recentAc($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    title titleSlug timestamp
  }
}
"""

QUESTION_QUERY = """
query question($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    title titleSlug difficulty topicTags { name }
  }
}
"""


class LeetCodeError(Exception):
    """LeetCode was unreachable, returned an error, or didn't have what we asked for."""


@dataclass
class RecentAc:
    title: str
    title_slug: str
    solved_at: datetime  # UTC


@dataclass
class QuestionInfo:
    title: str
    title_slug: str
    difficulty: str
    topics: list[str]


def _post_graphql(query: str, variables: dict) -> dict:
    """Send a GraphQL query and return its "data" object.

    Network problems and bad status codes are retried once. GraphQL "errors"
    are not retried, because asking again would give the same answer.
    """
    last_error = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = httpx.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=HEADERS,
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            body = response.json()
            break
        except (httpx.HTTPError, ValueError) as error:  # ValueError = response wasn't JSON
            logger.warning("LeetCode request failed (attempt {}): {}", attempt, error)
            last_error = error
    else:
        raise LeetCodeError(f"could not reach LeetCode: {last_error}")

    if body.get("errors"):
        raise LeetCodeError(body["errors"][0].get("message", "unknown GraphQL error"))
    return body.get("data") or {}


def get_recent_accepted(username: str, limit: int = 20) -> list[RecentAc]:
    """Return the user's most recent accepted submissions, newest first."""
    data = _post_graphql(RECENT_AC_QUERY, {"username": username, "limit": limit})

    submissions = data.get("recentAcSubmissionList")
    if submissions is None:  # LeetCode returns null for a username that doesn't exist
        raise LeetCodeError("user not found")

    return [
        RecentAc(
            title=item["title"],
            title_slug=item["titleSlug"],
            # timestamp is a *string* of Unix seconds, e.g. "1791468180"
            solved_at=datetime.fromtimestamp(int(item["timestamp"]), UTC),
        )
        for item in submissions
    ]


def get_question(slug: str) -> QuestionInfo:
    """Look up a problem's title, difficulty, and topics."""
    data = _post_graphql(QUESTION_QUERY, {"titleSlug": slug})

    question = data.get("question")
    if question is None:
        raise LeetCodeError(f"problem '{slug}' not found")

    return QuestionInfo(
        title=question["title"],
        title_slug=question["titleSlug"],
        difficulty=question["difficulty"],
        topics=[tag["name"] for tag in question["topicTags"]],
    )
