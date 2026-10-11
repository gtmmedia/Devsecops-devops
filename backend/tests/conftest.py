"""Shared fixtures.

Tests never touch PostgreSQL: they use a throw-away in-memory SQLite database,
and the FastAPI `get_db` dependency is overridden to point at it.
"""

import os

# Must be set before `app` is imported so the module-level engine is harmless.
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import metrics  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared in-memory DB for the whole test
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    original_factory = metrics.collector.session_factory
    metrics.collector.session_factory = TestingSession
    try:
        yield TestClient(app)
    finally:
        metrics.collector.session_factory = original_factory
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def ticket_payload():
    return {
        "title": "Invoice shows the wrong amount",
        "description": "We were charged twice in March.",
        "priority": "high",
        "requester_name": "Asha Rao",
        "requester_email": "asha@example.com",
    }


@pytest.fixture()
def make_ticket(client, ticket_payload):
    def _make(**overrides):
        response = client.post("/api/tickets", json={**ticket_payload, **overrides})
        assert response.status_code == 201, response.text
        return response.json()

    return _make
