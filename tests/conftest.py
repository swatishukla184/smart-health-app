"""Pytest fixtures and test client configuration."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.firestore_client import repo


@pytest.fixture(autouse=True)
def reset_database():
    """Resets in-memory storage to baseline seed data before each test."""
    repo.reset_for_tests()
    yield
    repo.reset_for_tests()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client
