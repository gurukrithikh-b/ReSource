"""
Phase 4 Step 2 Tests — Optimization API Integration
====================================================
Integration tests for the FastAPI optimization endpoints:
  - POST /api/v1/optimization/run
  - GET  /api/v1/optimization/summary

Uses an in-memory SQLite database via SQLAlchemy dependency overrides to ensure
isolated, reproducible, and deterministic test runs.

Coverage:
  1. OpenAPI registration of /optimization/run and /optimization/summary
  2. POST /optimization/run on empty DB → returns status NO_DATA (200 OK)
  3. GET /optimization/summary on empty DB → returns status NO_DATA (200 OK)
  4. Single surplus + single demand → status OPTIMAL, allocated 50 kg, enriched display names
  5. GET /optimization/summary with active match → status OPTIMAL, summary metrics
  6. Supply constraint → partial allocation when supply < demand
  7. Demand constraint → caps allocation at demand requirement when supply > demand
  8. Expired surplus listing → excluded from solver input
  9. Fully fulfilled demand listing → excluded from solver input
  10. Incompatible categories → no viable matches, returns status NO_DATA
  11. Storage incompatibility → disqualified, returns status NO_DATA
  12. Multi-point distribution → multiple suppliers & receivers optimized
  13. Zero remaining quantity surplus → excluded from solver input
  14. Schema validation — response includes all expected enriched fields
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app as fastapi_app
from app.core.database import Base, get_db
from app.models.organization import Organization, OrganizationType
from app.models.category import Category
from app.models.surplus import SurplusListing, SurplusStatus, StorageCondition
from app.models.demand import DemandListing, DemandStatus, UrgencyLevel
from sqlalchemy.pool import StaticPool


# Create in-memory SQLite database engine with StaticPool so all connections share the same memory DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables in memory for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # Override get_db dependency
    def _override_get_db():
        try:
            yield session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db_session):
    return TestClient(fastapi_app)



# ---------------------------------------------------------------------------
# Helper function to seed test data
# ---------------------------------------------------------------------------

def seed_basic_scenario(
    db,
    surplus_qty=50.0,
    demand_qty=50.0,
    demand_fulfilled=0.0,
    surplus_storage=StorageCondition.AMBIENT,
    demand_storage="AMBIENT",
    surplus_expires_hours=24,
    surplus_cat_name="Cooked Meals",
    demand_cat_name="Cooked Meals",
):
    """Seed a supplier org, receiver org, categories, surplus and demand listing."""
    # 1. Supplier Org
    supplier = Organization(
        id="org-sup-1",
        name="Hotel Grand Palace",
        org_type=OrganizationType.HOTEL,
        address="123 MG Road, Bengaluru",
        latitude=12.9716,
        longitude=77.5946,
    )
    # 2. Receiver Org
    receiver = Organization(
        id="org-rec-1",
        name="Hope Shelter NGO",
        org_type=OrganizationType.NGO,
        address="456 Indiranagar, Bengaluru",
        latitude=12.9652,
        longitude=77.6042,
    )
    db.add(supplier)
    db.add(receiver)

    # 3. Categories
    cat_sup = db.query(Category).filter(Category.name == surplus_cat_name).first()
    if not cat_sup:
        cat_sup = Category(id=f"cat-{surplus_cat_name.lower().replace(' ', '-')}", name=surplus_cat_name)
        db.add(cat_sup)

    if demand_cat_name == surplus_cat_name:
        cat_rec = cat_sup
    else:
        cat_rec = db.query(Category).filter(Category.name == demand_cat_name).first()
        if not cat_rec:
            cat_rec = Category(id=f"cat-{demand_cat_name.lower().replace(' ', '-')}", name=demand_cat_name)
            db.add(cat_rec)

    db.commit()

    now = datetime.utcnow()
    expires_at = now + timedelta(hours=surplus_expires_hours)

    # 4. Surplus Listing
    surplus = SurplusListing(
        id="surplus-1",
        supplier_id=supplier.id,
        category_id=cat_sup.id,
        title="Excess Dinner Buffet Curry & Rice",
        quantity=surplus_qty,
        remaining_quantity=surplus_qty,
        unit="kg",
        perishability_hours=24.0,
        storage_condition=surplus_storage,
        expires_at=expires_at,
        status=SurplusStatus.AVAILABLE,
    )

    # 5. Demand Listing
    demand = DemandListing(
        id="demand-1",
        receiver_id=receiver.id,
        category_id=cat_rec.id,
        title="Night Meal Program Needs",
        requested_quantity=demand_qty,
        fulfilled_quantity=demand_fulfilled,
        unit="kg",
        urgency_level=UrgencyLevel.HIGH,
        storage_capacity=demand_storage,
        required_by=now + timedelta(hours=12),
        status=DemandStatus.OPEN,
    )

    db.add(surplus)
    db.add(demand)
    db.commit()

    return supplier, receiver, surplus, demand


# ===========================================================================
# Test Cases
# ===========================================================================

class TestOptimizationEndpointsRegistration:
    def test_openapi_routes_registered(self, client):
        resp = client.get("/api/v1/openapi.json")
        assert resp.status_code == 200
        paths = resp.json().get("paths", {})
        assert "/api/v1/optimization/run" in paths
        assert "/api/v1/optimization/summary" in paths


class TestEmptyDatabaseBehaviors:
    def test_run_empty_db_returns_no_data(self, client):
        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_DATA"
        assert data["total_allocated"] == 0.0
        assert len(data["allocations"]) == 0

    def test_summary_empty_db_returns_no_data(self, client):
        resp = client.get("/api/v1/optimization/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_DATA"
        assert data["total_allocated"] == 0.0


class TestSingleMatchOptimization:
    def test_run_single_match_success(self, client, db_session):
        seed_basic_scenario(db_session, surplus_qty=50.0, demand_qty=50.0)

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "OPTIMAL"
        assert data["total_supply_available"] == 50.0
        assert data["total_demand_requested"] == 50.0
        assert data["total_allocated"] == 50.0
        assert data["total_unallocated"] == 0.0
        assert data["total_unmet_demand"] == 0.0
        assert data["num_allocations"] == 1
        assert data["num_demands_fully_satisfied"] == 1

        alloc = data["allocations"][0]
        assert alloc["surplus_id"] == "surplus-1"
        assert alloc["demand_id"] == "demand-1"
        assert alloc["allocated_quantity"] == 50.0
        assert alloc["match_score"] > 0
        assert alloc["supplier_name"] == "Hotel Grand Palace"
        assert alloc["receiver_name"] == "Hope Shelter NGO"
        assert alloc["category_name"] == "Cooked Meals"
        assert alloc["surplus_title"] == "Excess Dinner Buffet Curry & Rice"
        assert alloc["demand_title"] == "Night Meal Program Needs"

    def test_summary_single_match_success(self, client, db_session):
        seed_basic_scenario(db_session, surplus_qty=50.0, demand_qty=50.0)

        resp = client.get("/api/v1/optimization/summary")
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "OPTIMAL"
        assert data["total_allocated"] == 50.0
        assert data["num_allocations"] == 1
        assert data["num_demands_fully_satisfied"] == 1


class TestOptimizationConstraints:
    def test_supply_constraint_partial_allocation(self, client, db_session):
        # Surplus 30 kg, Demand 100 kg -> solver can only allocate 30 kg
        seed_basic_scenario(db_session, surplus_qty=30.0, demand_qty=100.0)

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "OPTIMAL"
        assert data["total_allocated"] == 30.0
        assert data["total_unallocated"] == 0.0
        assert data["total_unmet_demand"] == 70.0
        assert data["num_demands_partially_satisfied"] == 1

        alloc = data["allocations"][0]
        assert alloc["allocated_quantity"] == 30.0
        assert alloc["status"] == "PARTIALLY_ALLOCATED"

    def test_demand_constraint_caps_allocation(self, client, db_session):
        # Surplus 100 kg, Demand 40 kg -> solver caps allocation at 40 kg
        seed_basic_scenario(db_session, surplus_qty=100.0, demand_qty=40.0)

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "OPTIMAL"
        assert data["total_allocated"] == 40.0
        assert data["total_unallocated"] == 60.0
        assert data["total_unmet_demand"] == 0.0
        assert data["num_demands_fully_satisfied"] == 1

        alloc = data["allocations"][0]
        assert alloc["allocated_quantity"] == 40.0
        assert alloc["status"] == "ALLOCATED"


class TestDisqualificationFiltering:
    def test_expired_surplus_excluded(self, client, db_session):
        # Surplus expires in past (-2 hours)
        seed_basic_scenario(db_session, surplus_expires_hours=-2)

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_DATA"
        assert len(data["allocations"]) == 0

    def test_fulfilled_demand_excluded(self, client, db_session):
        # Demand requested 50 kg, already fulfilled 50 kg
        seed_basic_scenario(db_session, surplus_qty=50.0, demand_qty=50.0, demand_fulfilled=50.0)

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_DATA"
        assert len(data["allocations"]) == 0

    def test_incompatible_categories_excluded(self, client, db_session):
        # Surplus "Cooked Meals", Demand "Medical Supplies"
        seed_basic_scenario(
            db_session,
            surplus_cat_name="Cooked Meals",
            demand_cat_name="Medical Supplies",
        )

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_DATA"
        assert len(data["allocations"]) == 0

    def test_incompatible_storage_excluded(self, client, db_session):
        # Surplus FROZEN, Demand capacity AMBIENT
        seed_basic_scenario(
            db_session,
            surplus_storage=StorageCondition.FROZEN,
            demand_storage="AMBIENT",
        )

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_DATA"
        assert len(data["allocations"]) == 0

    def test_zero_remaining_quantity_surplus_excluded(self, client, db_session):
        seed_basic_scenario(db_session, surplus_qty=0.0, demand_qty=50.0)

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "NO_DATA"


class TestMultiPointAllocation:
    def test_multi_supplier_multi_receiver_optimized(self, client, db_session):
        # Seed 2 Suppliers, 2 Receivers, 2 Surplus, 2 Demands
        cat = Category(id="cat-raw-produce", name="Raw Produce")
        db_session.add(cat)

        sup1 = Organization(id="sup-1", name="Farm A", org_type=OrganizationType.INSTITUTION, address="Loc 1", latitude=12.97, longitude=77.59)
        sup2 = Organization(id="sup-2", name="Farm B", org_type=OrganizationType.INSTITUTION, address="Loc 2", latitude=12.98, longitude=77.60)
        rec1 = Organization(id="rec-1", name="Shelter X", org_type=OrganizationType.COMMUNITY_SHELTER, address="Loc 3", latitude=12.96, longitude=77.61)
        rec2 = Organization(id="rec-2", name="Shelter Y", org_type=OrganizationType.FOOD_BANK, address="Loc 4", latitude=12.95, longitude=77.62)
        db_session.add_all([sup1, sup2, rec1, rec2])
        db_session.commit()

        now = datetime.utcnow()
        exp = now + timedelta(hours=24)
        req = now + timedelta(hours=12)

        s1 = SurplusListing(id="s1", supplier_id="sup-1", category_id=cat.id, title="Apples 50kg", quantity=50.0, remaining_quantity=50.0, unit="kg", perishability_hours=24.0, expires_at=exp, status=SurplusStatus.AVAILABLE)
        s2 = SurplusListing(id="s2", supplier_id="sup-2", category_id=cat.id, title="Carrots 30kg", quantity=30.0, remaining_quantity=30.0, unit="kg", perishability_hours=24.0, expires_at=exp, status=SurplusStatus.AVAILABLE)

        d1 = DemandListing(id="d1", receiver_id="rec-1", category_id=cat.id, title="Produce Need 40kg", requested_quantity=40.0, fulfilled_quantity=0.0, unit="kg", urgency_level=UrgencyLevel.HIGH, required_by=req, status=DemandStatus.OPEN)
        d2 = DemandListing(id="d2", receiver_id="rec-2", category_id=cat.id, title="Produce Need 40kg", requested_quantity=40.0, fulfilled_quantity=0.0, unit="kg", urgency_level=UrgencyLevel.MEDIUM, required_by=req, status=DemandStatus.OPEN)

        db_session.add_all([s1, s2, d1, d2])
        db_session.commit()

        resp = client.post("/api/v1/optimization/run")
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "OPTIMAL"
        assert data["total_supply_available"] == 80.0
        assert data["total_demand_requested"] == 80.0
        assert data["total_allocated"] == 80.0
        assert data["num_allocations"] >= 2
        assert data["num_demands_fully_satisfied"] == 2
