"""
Tests for Chat API
====================
"""

import pytest
from fastapi.testclient import TestClient

from run import app


client = TestClient(app)


def test_root():
    """Test root endpoint returns app info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data


def test_health_check():
    """Test health endpoint returns healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


def test_chat_endpoint():
    """Test chat endpoint with a basic message."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "Halo, apa potensi angin di Pandeglang?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "model" in data
    assert len(data["reply"]) > 0


def test_chat_with_context():
    """Test chat endpoint with dashboard context."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Berikan analisis kecepatan angin",
            "context": {"site": "Pandeglang", "page": "wind-prediction"},
            "conversation_history": [],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data


def test_chat_empty_message():
    """Test chat endpoint rejects empty messages."""
    response = client.post(
        "/api/v1/chat",
        json={"message": ""},
    )
    assert response.status_code == 422
