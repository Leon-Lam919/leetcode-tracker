import pytest

from config import Settings


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_timezone_fails_fast():
    with pytest.raises(ValueError, match="not a valid IANA timezone"):
        Settings(tz="Mars/Olympus_Mons")


def test_cors_origins_are_comma_separated():
    settings = Settings(cors_origins=" http://localhost:5174, http://localhost:5173 ,")
    assert settings.cors_origin_list == ["http://localhost:5174", "http://localhost:5173"]


def test_cors_allows_the_default_origin(client):
    response = client.get("/api/health", headers={"Origin": "http://localhost:5174"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:5174"

    response = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in response.headers
