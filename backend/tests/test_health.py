import pytest

from config import Settings


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_timezone_fails_fast():
    with pytest.raises(ValueError, match="not a valid IANA timezone"):
        Settings(tz="Mars/Olympus_Mons")
