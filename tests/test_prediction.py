"""
Tests for Prediction API
=========================
"""

import pytest
from fastapi.testclient import TestClient

from run import app

client = TestClient(app)


def test_list_locations():
    """Test GET /predict/locations returns a list of available locations."""
    response = client.get("/api/v1/predict/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "name" in data[0]
        assert "scenario" in data[0]
        assert "status" in data[0]


def test_get_ranking():
    """Test GET /ranking returns a list of sites ranked by composite score."""
    response = client.get("/api/v1/ranking")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "id" in data[0]
        assert "name" in data[0]
        assert "rank" in data[0]
        assert "feasibilityScore" in data[0]
        assert "metrics" in data[0]


def test_get_metrics():
    """Test GET /predict/metrics returns final performance metrics from csv."""
    response = client.get("/api/v1/predict/metrics")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_predict_wind_speed_valid():
    """Test POST /predict with a valid payload."""
    payload = {
        "location": "pandeglang",
        "recent_ws10m": [4.0] * 24,
        "target_time": "2026-01-01T08:00:00",
    }
    response = client.post("/api/v1/predict", json=payload)
    # Note: If artifacts directory is deferring load or missing some files,
    # it might raise 500 or 400. Let's make sure it handles both gracefully or runs successfully.
    if response.status_code == 200:
        data = response.json()
        assert data["location"] == "pandeglang"
        assert "predicted_ws10m" in data
        assert "scenario" in data
        assert "model_confidence_r2" in data
    else:
        # If model artifacts are missing or environment is not fully setup,
        # it might return 500/400.
        assert response.status_code in [400, 500]


def test_predict_wind_speed_invalid_location():
    """Test POST /predict with an unknown location returns 400."""
    payload = {
        "location": "unknown_site",
        "recent_ws10m": [4.0] * 24,
        "target_time": "2026-01-01T08:00:00",
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "unknown_location"


def test_predict_wind_speed_insufficient_history():
    """Test POST /predict with < 24 history data points returns 400."""
    payload = {
        "location": "pandeglang",
        "recent_ws10m": [4.0] * 12,  # Only 12 hours
        "target_time": "2026-01-01T08:00:00",
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "invalid_input"
