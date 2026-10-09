from datetime import timedelta

from sqlmodel import func, select

import db
from models.tables import PatternList, PatternProblem
from services.clock import today_local
from services.patterns import seed_lists

ALL_PATTERNS = [
    "Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack", "Binary Search",
    "Linked List", "Trees", "Heap / Priority Queue", "Backtracking", "Tries", "Graphs",
    "Advanced Graphs", "1-D Dynamic Programming", "2-D Dynamic Programming", "Greedy",
    "Intervals", "Math & Geometry", "Bit Manipulation",
]  # fmt: skip


def count(session, model):
    return session.exec(select(func.count()).select_from(model)).one()


def test_startup_seeds_neetcode_150_once(engine, session):
    # The `engine` fixture already ran startup once. Run the seed and startup again.
    seed_lists(engine)
    db.create_db_and_tables()

    assert count(session, PatternList) == 1
    assert count(session, PatternProblem) == 150


def test_endpoint_shape_and_order(client):
    groups = client.get("/api/patterns?list=neetcode150").json()

    assert [group["pattern"] for group in groups] == ALL_PATTERNS
    assert sum(group["total"] for group in groups) == 150
    first = groups[0]
    assert first["total"] == len(first["problems"]) == 9
    assert first["solved"] == 0
    assert first["problems"][0] == {
        "slug": "contains-duplicate",
        "title": "Contains Duplicate",
        "difficulty": "Easy",
        "url": "https://leetcode.com/problems/contains-duplicate/",
        "solved": False,
        "needs_review": False,
    }


def test_default_list_is_neetcode150(client):
    assert client.get("/api/patterns").json() == client.get("/api/patterns?list=neetcode150").json()


def test_unknown_list_is_404(client):
    assert client.get("/api/patterns?list=blind75").status_code == 404


def test_solved_is_joined_on_slug(client):
    two_days_ago = (today_local() - timedelta(days=2)).isoformat()
    client.post(
        "/api/solves",
        json={
            "title_slug": "two-sum",
            "title": "Two Sum",
            "difficulty": "Easy",
            "solved_date": two_days_ago,
        },
    )
    # A solve that isn't on the list doesn't count anywhere.
    client.post(
        "/api/solves",
        json={"title_slug": "fizz-buzz", "title": "Fizz Buzz", "difficulty": "Easy"},
    )

    groups = {group["pattern"]: group for group in client.get("/api/patterns").json()}
    arrays = groups["Arrays & Hashing"]
    two_sum = next(p for p in arrays["problems"] if p["slug"] == "two-sum")

    assert arrays["solved"] == 1
    assert two_sum["solved"] is True
    assert two_sum["needs_review"] is True  # first review was due the day after the solve
    assert sum(group["solved"] for group in groups.values()) == 1


def test_needs_review_flag_on_a_solve_counts(client):
    client.post(
        "/api/solves",
        json={"title_slug": "3sum", "title": "3Sum", "difficulty": "Medium", "needs_review": True},
    )
    groups = {group["pattern"]: group for group in client.get("/api/patterns").json()}
    three_sum = next(p for p in groups["Two Pointers"]["problems"] if p["slug"] == "3sum")
    assert three_sum["solved"] is True
    assert three_sum["needs_review"] is True
