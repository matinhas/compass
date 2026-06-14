from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    with patch("app.database.db.create_engine", return_value=MagicMock()):
        with patch("app.database.db.SessionLocal", return_value=MagicMock()):
            from app.main import app
            return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
