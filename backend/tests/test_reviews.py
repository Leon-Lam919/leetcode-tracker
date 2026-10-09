"""Review queue: triggers, the due query, and the endpoints.

"Now" is faked by patching services.clock.utc_now. The test TZ is America/Toronto
(UTC-4 in October), so 04:00 UTC is local midnight.
"""

from datetime import UTC, datetime

import pytest

from services import clock

TWO_SUM = {"title_slug": "two-sum", "title": "Two Sum", "difficulty": "Easy"}


@pytest.fixture
def set_now(monkeypatch):
    def set_to(year, month, day, hour=16, minute=0):  # 16:00 UTC = noon in Toronto
        moment = datetime(year, month, day, hour, minute, tzinfo=UTC)
        monkeypatch.setattr(clock, "utc_now", lambda: moment)

    set_to(2026, 10, 8)
    return set_to


def add(client, solved_date, **fields):
    body = {**TWO_SUM, "solved_date": solved_date, **fields}
    response = client.post("/api/solves", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def due_slugs(client):
    return [item["title_slug"] for item in client.get("/api/reviews/due").json()]


# --- Triggers ---------------------------------------------------------------


def test_first_solve_is_due_the_next_day(client, set_now):
    add(client, "2026-10-08")
    assert due_slugs(client) == []  # not today

    set_now(2026, 10, 9)
    due = client.get("/api/reviews/due").json()
    assert [item["title_slug"] for item in due] == ["two-sum"]
    assert due[0]["next_review_date"] == "2026-10-09"
    assert due[0]["days_overdue"] == 0


def test_sync_puts_two_sum_in_the_queue_tomorrow(client, set_now):
    # The sync fixture has Two Sum accepted on 2026-10-08 (Toronto time).
    client.post("/api/sync")
    assert "two-sum" not in due_slugs(client)

    set_now(2026, 10, 9)
    assert "two-sum" in due_slugs(client)


def test_resolve_on_a_later_day_counts_as_a_review(client, set_now):
    add(client, "2026-10-01")
    add(client, "2026-10-08", confidence=3)  # easy: index 0 -> 2, 7 days

    upcoming = client.get("/api/reviews/upcoming?days=7").json()
    assert {day["date"]: day["count"] for day in upcoming}["2026-10-15"] == 1
    assert due_slugs(client) == []


def test_resolve_without_confidence_counts_as_good(client, set_now):
    add(client, "2026-10-05")
    add(client, "2026-10-08")  # good: index 0 -> 1, 3 days

    set_now(2026, 10, 11)
    assert client.get("/api/reviews/due").json()[0]["next_review_date"] == "2026-10-11"


def test_older_solve_added_later_does_not_reschedule(client, set_now):
    add(client, "2026-10-08")
    add(client, "2026-09-01", confidence=1)

    set_now(2026, 10, 9)
    assert client.get("/api/reviews/due").json()[0]["next_review_date"] == "2026-10-09"


def test_sync_resolve_counts_as_review(client, set_now, fake_leetcode):
    add(client, "2026-10-01")  # Two Sum first solved a week before the synced re-solve
    client.post("/api/sync")

    set_now(2026, 10, 10)  # the re-solve on 10-08 moved it to 10-11 (good = 3 days)
    assert "two-sum" not in due_slugs(client)
    set_now(2026, 10, 11)
    assert "two-sum" in due_slugs(client)


def test_patching_confidence_does_not_reschedule(client, set_now):
    solve = add(client, "2026-10-08")
    client.patch(f"/api/solves/{solve['id']}", json={"confidence": 1})

    set_now(2026, 10, 9)
    assert due_slugs(client) == ["two-sum"]
    set_now(2026, 10, 8)
    assert due_slugs(client) == []


def test_deleting_the_only_solve_removes_the_review(client, set_now):
    solve = add(client, "2026-10-01")
    assert due_slugs(client) == ["two-sum"]

    client.delete(f"/api/solves/{solve['id']}")
    assert due_slugs(client) == []


# --- Due query --------------------------------------------------------------


def test_due_respects_the_local_day_boundary(client, set_now):
    add(client, "2026-10-08")  # due 2026-10-09 (local)

    set_now(2026, 10, 9, hour=3, minute=59)  # 23:59 on Oct 8 in Toronto
    assert due_slugs(client) == []

    set_now(2026, 10, 9, hour=4, minute=0)  # 00:00 on Oct 9 in Toronto
    assert due_slugs(client) == ["two-sum"]


def test_due_is_oldest_first_with_details(client, set_now):
    add(client, "2026-10-06")
    solve = add(
        client, "2026-10-03", title_slug="3sum", title="3Sum", difficulty="Medium", confidence=2
    )
    client.patch(f"/api/solves/{solve['id']}", json={"approach": "sort + two pointers"})

    due = client.get("/api/reviews/due").json()

    assert [item["title_slug"] for item in due] == ["3sum", "two-sum"]
    first = due[0]
    assert first["days_overdue"] == 4  # due Oct 4, today Oct 8
    assert first["difficulty"] == "Medium"
    assert first["url"] == "https://leetcode.com/problems/3sum/"
    assert first["last_confidence"] == 2
    assert first["approach"] == "sort + two pointers"
    assert due[1]["approach"] is None


def test_stats_counts_reviews_due(client, set_now):
    add(client, "2026-10-01")
    add(client, "2026-10-08", title_slug="3sum", title="3Sum")
    assert client.get("/api/stats").json()["reviews_due"] == 1


# --- POST /api/reviews/{problem_id} ----------------------------------------


@pytest.mark.parametrize(
    ("confidence", "next_date"),
    [(1, "2026-10-09"), (2, "2026-10-11"), (3, "2026-10-15")],
)
def test_mark_reviewed(client, set_now, confidence, next_date):
    problem_id = add(client, "2026-10-01")["id"]  # solve id 1 == problem id 1 here

    response = client.post(f"/api/reviews/{problem_id}", json={"confidence": confidence})

    assert response.status_code == 200
    body = response.json()
    assert body["next_review_date"] == next_date
    assert body["last_reviewed_date"] == "2026-10-08"
    assert body["last_confidence"] == confidence
    assert due_slugs(client) == []


def test_mark_reviewed_until_mastered(client, set_now):
    add(client, "2026-10-01")
    for _ in range(3):  # easy: 0 -> 2 -> 4 -> mastered
        body = client.post("/api/reviews/1", json={"confidence": 3}).json()
    assert body["next_review_date"] is None
    assert body["interval_index"] == 4


def test_mark_reviewed_unknown_problem_is_404(client):
    assert client.post("/api/reviews/999", json={"confidence": 2}).status_code == 404


@pytest.mark.parametrize("body", [{"confidence": 0}, {"confidence": 4}, {}])
def test_mark_reviewed_validates_confidence(client, body):
    add(client, "2026-10-01")
    assert client.post("/api/reviews/1", json=body).status_code == 422


def test_upcoming_has_one_entry_per_day(client, set_now):
    add(client, "2026-10-08")
    upcoming = client.get("/api/reviews/upcoming").json()
    assert len(upcoming) == 7
    assert upcoming[0] == {"date": "2026-10-09", "count": 1}
    assert sum(day["count"] for day in upcoming) == 1
