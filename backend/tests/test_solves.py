from datetime import date, timedelta

from services.clock import today_local

TWO_SUM = {
    "title_slug": "two-sum",
    "title": "Two Sum",
    "difficulty": "Easy",
    "topics": ["Array", "Hash Table"],
}


def add(client, **overrides):
    """POST a manual solve (Two Sum unless overridden) and return the response."""
    return client.post("/api/solves", json={**TWO_SUM, **overrides})


def test_manual_add_returns_solve_out(client):
    response = add(client, notes="used a dict", confidence=3)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Two Sum"
    assert body["topics"] == ["Array", "Hash Table"]
    assert body["url"] == "https://leetcode.com/problems/two-sum/"
    assert body["source"] == "manual"
    assert body["solved_date"] == today_local().isoformat()
    assert body["solved_at"].endswith("Z")
    assert body["notes"] == "used a dict"
    assert body["confidence"] == 3
    assert body["needs_review"] is False


def test_same_problem_same_day_is_409(client):
    assert add(client).status_code == 201
    response = add(client)
    assert response.status_code == 409
    assert "already logged" in response.json()["detail"]


def test_same_problem_different_day_is_allowed(client):
    yesterday = (today_local() - timedelta(days=1)).isoformat()
    assert add(client).status_code == 201
    assert add(client, solved_date=yesterday).status_code == 201


def test_manual_add_looks_up_problem_on_leetcode(client, fake_leetcode):
    response = client.post("/api/solves", json={"title_slug": "valid-parentheses"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Valid Parentheses"
    assert body["difficulty"] == "Easy"
    assert body["topics"] == ["String", "Stack"]
    assert fake_leetcode.calls == ["question"]


def test_manual_add_falls_back_to_body_when_lookup_fails(client, fake_leetcode):
    fake_leetcode.down = True
    response = add(client)  # body includes title, difficulty, topics
    assert response.status_code == 201
    assert response.json()["title"] == "Two Sum"


def test_manual_add_with_failed_lookup_and_no_details_is_502(client, fake_leetcode):
    response = client.post("/api/solves", json={"title_slug": "made-up-problem"})
    assert response.status_code == 502
    assert "title and difficulty" in response.json()["detail"]


def test_known_problem_is_not_looked_up_again(client, fake_leetcode):
    yesterday = (today_local() - timedelta(days=1)).isoformat()
    client.post("/api/solves", json={"title_slug": "two-sum", "solved_date": yesterday})
    client.post("/api/solves", json={"title_slug": "two-sum"})
    assert fake_leetcode.calls == ["question"]


def test_list_is_newest_first(client):
    add(client, solved_date="2026-01-01")
    add(client, title_slug="valid-anagram", title="Valid Anagram", solved_date="2026-01-03")
    add(client, title_slug="3sum", title="3Sum", difficulty="Medium", solved_date="2026-01-02")

    dates = [solve["solved_date"] for solve in client.get("/api/solves").json()]
    assert dates == ["2026-01-03", "2026-01-02", "2026-01-01"]


def test_list_filters(client):
    add(client)
    add(client, title_slug="3sum", title="3Sum", difficulty="Medium", topics=["Two Pointers"])
    add(client, title_slug="lru-cache", title="LRU Cache", difficulty="Hard", needs_review=True)

    def slugs(query):
        return [solve["title_slug"] for solve in client.get(f"/api/solves?{query}").json()]

    assert slugs("difficulty=Medium") == ["3sum"]
    assert slugs("topic=Two%20Pointers") == ["3sum"]
    assert slugs("needs_review=true") == ["lru-cache"]
    assert len(slugs("")) == 3


def test_patch_updates_only_sent_fields(client):
    solve_id = add(client, notes="first try").json()["id"]

    response = client.patch(f"/api/solves/{solve_id}", json={"confidence": 1, "needs_review": True})

    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == 1
    assert body["needs_review"] is True
    assert body["notes"] == "first try"  # untouched


def test_patch_validates_fields(client):
    solve_id = add(client).json()["id"]
    assert client.patch(f"/api/solves/{solve_id}", json={"confidence": 4}).status_code == 422
    assert client.patch(f"/api/solves/{solve_id}", json={"time_spent_min": -5}).status_code == 422


def test_patch_missing_is_404(client):
    assert client.patch("/api/solves/999", json={"notes": "x"}).status_code == 404


def test_delete(client):
    solve_id = add(client).json()["id"]
    assert client.delete(f"/api/solves/{solve_id}").status_code == 204
    assert client.get("/api/solves").json() == []
    assert client.delete(f"/api/solves/{solve_id}").status_code == 404


def test_solved_date_is_a_plain_date(client):
    body = add(client, solved_date="2026-03-08").json()
    assert date.fromisoformat(body["solved_date"]) == date(2026, 3, 8)
