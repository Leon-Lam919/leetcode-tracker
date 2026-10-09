from tests.conftest import load_fixture


def test_sync_adds_recent_solves(client, fake_leetcode):
    response = client.post("/api/sync")

    assert response.status_code == 200
    # 4 submissions, but Two Sum was accepted twice on the same day: 3 added, 1 skipped.
    assert response.json() == {"added": 3, "skipped": 1}

    solves = {solve["title_slug"]: solve for solve in client.get("/api/solves").json()}
    assert set(solves) == {"valid-parentheses", "two-sum", "add-two-numbers"}
    assert solves["two-sum"]["source"] == "sync"
    assert solves["add-two-numbers"]["difficulty"] == "Medium"


def test_sync_uses_local_date(client):
    client.post("/api/sync")
    solves = {solve["title_slug"]: solve for solve in client.get("/api/solves").json()}

    # 03:00 UTC on Oct 8 is 23:00 on Oct 7 in Toronto (the test TZ).
    add_two = solves["add-two-numbers"]
    assert add_two["solved_at"] == "2026-10-08T03:00:00Z"
    assert add_two["solved_date"] == "2026-10-07"


def test_sync_is_idempotent(client):
    first = client.post("/api/sync").json()
    second = client.post("/api/sync").json()

    assert first["added"] == 3
    assert second == {"added": 0, "skipped": 4}
    assert len(client.get("/api/solves").json()) == 3


def test_sync_looks_up_each_new_problem_once(client, fake_leetcode):
    client.post("/api/sync")
    client.post("/api/sync")
    # 2 syncs, but only 3 question lookups total (one per new problem).
    assert fake_leetcode.calls.count("recentAc") == 2
    assert fake_leetcode.calls.count("question") == 3


def test_sync_never_overwrites_notes(client):
    client.post("/api/sync")
    two_sum = next(s for s in client.get("/api/solves").json() if s["title_slug"] == "two-sum")
    client.patch(f"/api/solves/{two_sum['id']}", json={"notes": "hash map trick", "confidence": 3})

    client.post("/api/sync")

    two_sum = next(s for s in client.get("/api/solves").json() if s["title_slug"] == "two-sum")
    assert two_sum["notes"] == "hash map trick"
    assert two_sum["confidence"] == 3


def test_sync_user_not_found_is_502(client, fake_leetcode):
    fake_leetcode.recent_response = load_fixture("recent_ac_user_not_found.json")

    response = client.post("/api/sync")

    assert response.status_code == 502
    assert "user not found" in response.json()["detail"]


def test_sync_when_leetcode_is_down_is_502_and_saves_nothing(client, fake_leetcode):
    fake_leetcode.down = True
    response = client.post("/api/sync")
    assert response.status_code == 502
    assert client.get("/api/solves").json() == []


def test_sync_without_username_is_400(client, monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "leetcode_username", "")
    assert client.post("/api/sync").status_code == 400
