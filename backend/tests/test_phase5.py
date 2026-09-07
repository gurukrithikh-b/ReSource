"""
Phase 5 — Sustainability Impact Intelligence Unit & Integration Tests
====================================================================
Tests impact calculations, category CO2 factors, idempotency, API endpoints,
trends, category grouping, provider contribution, and community reach.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from main import app
from app.impact.impact_calculator import impact_calculator, ImpactCalculator
from app.models.impact import ImpactLog


# ---------------------------------------------------------------------------
# Setup In-Memory SQLite Test DB
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from app.models.impact import ensure_impact_table_schema
Base.metadata.create_all(bind=engine)
ensure_impact_table_schema(engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit Tests — ImpactCalculator Engine
# ---------------------------------------------------------------------------

def test_basic_impact_calculation():
    calc = ImpactCalculator()
    metrics = calc.calculate_metrics(100.0, "Cooked Meals")
    assert metrics["resource_recovered_kg"] == 100.0
    assert metrics["demand_fulfilled_kg"] == 100.0
    assert metrics["meals_provided_estimate"] == 250.0  # 100 / 0.4
    assert metrics["co2_avoided_kg"] == 250.0  # 100 * 2.5


def test_category_factors_and_fallback():
    calc = ImpactCalculator()
    assert calc.get_category_co2_factor("Fresh Produce") == 1.9
    assert calc.get_category_co2_factor("Meat") == 6.5
    assert calc.get_category_co2_factor("Bakery Items") == 1.2
    assert calc.get_category_co2_factor("Unknown Category X") == 2.5  # Fallback
    assert calc.get_category_co2_factor(None) == 2.5  # None fallback


def test_zero_and_invalid_allocation_quantity():
    calc = ImpactCalculator()
    metrics = calc.calculate_metrics(0.0, "Cooked Meals")
    assert metrics["resource_recovered_kg"] == 0.0
    assert metrics["meals_provided_estimate"] == 0.0
    assert metrics["co2_avoided_kg"] == 0.0

    metrics_neg = calc.calculate_metrics(-50.0, "Fresh Produce")
    assert metrics_neg["resource_recovered_kg"] == 0.0


def test_idempotent_impact_logging():
    db = TestingSessionLocal()
    try:
        alloc_id = "test_alloc_id_101"
        # First creation
        log1 = impact_calculator.process_allocation_impact(
            db=db,
            allocation_id=alloc_id,
            allocated_quantity=100.0,
            category_name="Fresh Produce",
            supplier_name="Farm Direct",
            receiver_name="Community Shelter",
        )
        assert log1.id is not None
        assert log1.resource_recovered_kg == 100.0

        # Second creation with same allocation_id (Idempotent update)
        log2 = impact_calculator.process_allocation_impact(
            db=db,
            allocation_id=alloc_id,
            allocated_quantity=100.0,
            category_name="Fresh Produce",
            supplier_name="Farm Direct",
            receiver_name="Community Shelter",
        )
        assert log2.id == log1.id  # Same record ID, no duplicate row
        
        count = db.query(ImpactLog).filter(ImpactLog.allocation_id == alloc_id).count()
        assert count == 1
    finally:
        db.close()


# ---------------------------------------------------------------------------
# API Integration Tests — Phase 5 Endpoints
# ---------------------------------------------------------------------------

def test_api_calculate_impact_endpoint():
    payload = {
        "allocations": [
            {
                "allocation_id": "api_test_alloc_1",
                "allocated_quantity": 200.0,
                "category_name": "Cooked Meals",
                "supplier_name": "Hotel Grand",
                "receiver_name": "Hope Shelter",
            },
            {
                "allocation_id": "api_test_alloc_2",
                "allocated_quantity": 150.0,
                "category_name": "Bakery Items",
                "supplier_name": "City Bakery",
                "receiver_name": "Youth Food Bank",
            },
        ]
    }
    response = client.post("/api/v1/impact/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["co2_avoided_kg"] == 500.0  # 200 * 2.5
    assert data[1]["co2_avoided_kg"] == 180.0  # 150 * 1.2


def test_api_impact_summary_endpoint():
    response = client.get("/api/v1/impact/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_resources_rescued_kg" in data
    assert "total_demand_fulfilled_kg" in data
    assert "total_meals_served" in data
    assert "total_co2_avoided_kg" in data
    assert "unique_community_partners" in data


def test_api_impact_trends_endpoint():
    response = client.get("/api/v1/impact/trends?group_by=day")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_impact_categories_endpoint():
    response = client.get("/api/v1/impact/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "category" in data[0]
        assert "resources_rescued_kg" in data[0]


def test_api_impact_providers_endpoint():
    response = client.get("/api/v1/impact/providers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_api_impact_partners_endpoint():
    response = client.get("/api/v1/impact/partners")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
