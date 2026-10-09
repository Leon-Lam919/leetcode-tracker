from datetime import timedelta

import pytest

from config import settings
from services.clock import today_local


def add(client, slug, difficulty="Easy", topics=None, days_ago=0):
    solved_date = (today_local() - timedelta(days=days_ago)).isoformat()
    response = client.post(
        "/api/solves",
        json={
            "title_slug": slug,
            "title": slug.replace("-", " ").title(),
            "difficulty": difficulty,
            "topics": topics or [],
            "solved_date": solved_date,
        },
    )
    assert response.status_code == 201


def test_empty_stats(client):
    stats = client.get("/api/stats").json()
    assert stats == {
        "today_done": False,
        "today_count": 0,
        "daily_goal": 1,
        "current_streak": 0,
        "longest_streak": 0,
        "total_solved": 0,
        "by_difficulty": {"Easy": 0, "Medium": 0, "Hard": 0},
        "by_topic": {},
    }


def test_stats_with_solves(client):
    add(client, "two-sum", "Easy", ["Array", "Hash Table"], days_ago=0)
    add(client, "two-sum", "Easy", ["Array", "Hash Table"], days_ago=1)  # re-solve
    add(client, "3sum", "Medium", ["Array", "Two Pointers"], days_ago=2)

    stats = client.get("/api/stats").json()

    assert stats["today_done"] is True
    assert stats["today_count"] == 1
    assert stats["current_streak"] == 3
    assert stats["longest_streak"] == 3
    # Distinct problems: Two Sum counts once even though it was solved twice.
    assert stats["total_solved"] == 2
    assert stats["by_difficulty"] == {"Easy": 1, "Medium": 1, "Hard": 0}
    assert stats["by_topic"] == {"Array": 2, "Hash Table": 1, "Two Pointers": 1}


def test_daily_goal_is_respected(client, monkeypatch):
    monkeypatch.setattr(settings, "daily_goal", 2)
    add(client, "two-sum")

    stats = client.get("/api/stats").json()
    assert stats["today_done"] is False
    assert stats["current_streak"] == 0


def test_heatmap_default_is_90_days_oldest_first(client):
    add(client, "two-sum", days_ago=0)
    add(client, "3sum", days_ago=0)
    add(client, "valid-anagram", days_ago=5)

    heatmap = client.get("/api/heatmap").json()

    assert len(heatmap) == 90
    assert heatmap[-1] == {"date": today_local().isoformat(), "count": 2}
    assert heatmap[-6]["count"] == 1
    assert heatmap[0]["date"] == (today_local() - timedelta(days=89)).isoformat()
    assert sum(day["count"] for day in heatmap) == 3


@pytest.mark.parametrize("days", [0, 1000])
def test_heatmap_rejects_bad_days(client, days):
    assert client.get(f"/api/heatmap?days={days}").status_code == 422
