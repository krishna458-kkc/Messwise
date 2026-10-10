"""Tests for MessWise FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app, get_db_session
from messwise.db import Base, init_db


@pytest.fixture
def client():
    """Provides a TestClient with an isolated in-memory SQLite database."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    init_db(test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db_session():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_endpoint(client):
    """Test /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "MessWise"
    assert data["phase"] == 1


def test_log_meal_and_dish(client):
    """Test creating a meal, a dish, and logging dish leftovers via API."""
    # 1. Register dish
    dish_resp = client.post(
        "/dishes",
        json={"name": "Dal Tadka", "category": "staple", "unit": "L"},
    )
    assert dish_resp.status_code == 201
    dish_id = dish_resp.json()["dish"]["id"]

    # 2. Log meal
    meal_resp = client.post(
        "/log/meal",
        json={
            "date": "2026-10-15",
            "meal_type": "lunch",
            "headcount": 425,
            "hostel_strength": 500,
            "event_flag": 0,
            "exam_flag": 0,
            "holiday_flag": 0,
            "is_synthetic": 0,
        },
    )
    assert meal_resp.status_code == 201
    meal_id = meal_resp.json()["meal"]["id"]

    # 3. Log dish
    dish_log_resp = client.post(
        "/log/dish",
        json={
            "meal_id": meal_id,
            "dish_id": dish_id,
            "cooked_qty": 35.0,
            "leftover_qty": 3.0,
            "unit": "L",
            "ran_out": 0,
            "waste_stage": "serving_surplus",
            "reason_tag": "overproduction",
            "is_synthetic": 0,
        },
    )
    assert dish_log_resp.status_code == 201

    # 4. Query meal
    get_meal_resp = client.get(f"/meals/{meal_id}")
    assert get_meal_resp.status_code == 200
    meal_data = get_meal_resp.json()
    assert meal_data["meal"]["id"] == meal_id
    assert len(meal_data["dish_logs"]) == 1
    assert meal_data["dish_logs"][0]["cooked_qty"] == 35.0


def test_reject_invalid_meal_api(client):
    """Test that invalid meal data returns 422 Unprocessable Entity."""
    response = client.post(
        "/log/meal",
        json={
            "date": "2026-10-15",
            "meal_type": "lunch",
            "headcount": -10,  # Negative
            "hostel_strength": 500,
        },
    )
    assert response.status_code == 422


def test_reject_leftover_greater_than_cooked_api(client):
    """Test that leftover > cooked returns 422."""
    response = client.post(
        "/log/dish",
        json={
            "meal_id": 1,
            "dish_id": 1,
            "cooked_qty": 10.0,
            "leftover_qty": 20.0,  # > cooked
            "unit": "kg",
        },
    )
    assert response.status_code == 422


def test_forecast_and_placeholder_endpoints(client):
    """Test that /forecast and /plan are active, and /simulate is active for Step 5."""
    resp_forecast = client.get("/forecast?date=2026-10-15&meal_type=lunch")
    assert resp_forecast.status_code == 200
    assert "forecasts" in resp_forecast.json()

    # /plan is active (Step 3 B1-B3)
    resp_plan = client.post(
        "/plan",
        json={
            "date": "2026-10-15",
            "meal_type": "lunch",
            "service_level": 0.95,
            "prep_loss_pct": 0.03,
            "hostel_strength": 500,
            "is_synthetic": 0,
        },
    )
    assert resp_plan.status_code == 200
    plan_data = resp_plan.json()
    assert plan_data["status"] == "success"
    assert "plan" in plan_data
    assert plan_data["plan"]["service_level"] == 0.95
    assert "planning_headcount" in plan_data["plan"]

    # /simulate is active (Step 5 E3)
    resp_sim = client.post(
        "/simulate",
        json={
            "is_synthetic": 1,
            "service_level": 0.95,
            "hostel_strength": 500,
        },
    )
    assert resp_sim.status_code == 200
    sim_data = resp_sim.json()
    assert sim_data["status"] == "success"
    assert "report" in sim_data
    assert sim_data["report"]["cost_status_message"] == "Cost estimation unavailable — valid ingredient prices are not configured."



def test_plan_api_validation_errors(client):
    """Test validation errors on /plan endpoint."""
    # Missing required fields
    resp_empty = client.post("/plan", json={})
    assert resp_empty.status_code == 422

    # Invalid service level (> 0.999 or < 0.50)
    resp_bad_sl = client.post(
        "/plan",
        json={
            "date": "2026-10-15",
            "meal_type": "lunch",
            "service_level": 1.5,
        },
    )
    assert resp_bad_sl.status_code == 422

    # Invalid meal type
    resp_bad_meal = client.post(
        "/plan",
        json={
            "date": "2026-10-15",
            "meal_type": "midnight_snack",
            "service_level": 0.95,
        },
    )
    assert resp_bad_meal.status_code == 422


def test_api_csv_preview_and_import(client):
    """Test /kitchen/csv-preview and /kitchen/csv-import endpoints."""
    csv_bytes = b"date,meal_type,headcount,hostel_strength\n2026-10-20,lunch,350,500\n2026-10-20,dinner,340,500\n"

    # 1. Preview
    files = {"file": ("test.csv", csv_bytes, "text/csv")}
    resp_prev = client.post("/kitchen/csv-preview", files=files)
    assert resp_prev.status_code == 200
    prev_data = resp_prev.json()
    assert prev_data["status"] == "success"
    assert prev_data["preview"]["total_rows"] == 2

    # 2. Import
    files2 = {"file": ("test.csv", csv_bytes, "text/csv")}
    resp_imp = client.post("/kitchen/csv-import?is_synthetic=1&who=test_runner", files=files2)
    assert resp_imp.status_code == 200
    imp_data = resp_imp.json()
    assert imp_data["status"] == "success"
    assert imp_data["import_summary"]["accepted_rows"] == 2
    assert imp_data["import_summary"]["rejected_rows"] == 0

