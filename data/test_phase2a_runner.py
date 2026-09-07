import os
import sys

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from app.ai.nlp_parser import nlp_parser
from app.core.database import SessionLocal
from app.models.surplus import SurplusListing
from app.models.demand import DemandListing

def run_phase2a_runner():
    print("=" * 65)
    print("      ReSource HG - Phase 2A Final Verification Runner")
    print("=" * 65)

    client = TestClient(app)

    # 1. Test NLP Intake Parser & Timezone (Asia/Kolkata)
    print("\n[1] Testing Timezone-Aware NLP Intake Parser (Asia/Kolkata):")
    t1 = "We have 200 packed vegetarian meals available until 9 PM today. They need refrigeration."
    p1 = nlp_parser.parse_listing_text(t1)
    print(f"  Input: '{t1}'")
    print(f"  Result -> Qty: {p1['quantity']} {p1['unit']}, Storage: {p1['storage_condition']}, Deadline: {p1['deadline_display']}, Conf: {p1['confidence']}")
    assert p1["quantity"] == 200.0 and p1["unit"] == "meals" and p1["storage_condition"] == "REFRIGERATED"
    assert "9:00 PM" in p1["deadline_display"]

    t2 = "15 kg artisan bread loaves available for 24 hours."
    p2 = nlp_parser.parse_listing_text(t2)
    print(f"\n  Input: '{t2}'")
    print(f"  Result -> Qty: {p2['quantity']} {p2['unit']}, Storage: {p2['storage_condition']} (Null handled), Deadline: {p2['deadline_display']}")
    assert p2["quantity"] == 15.0 and p2["storage_condition"] is None

    t3 = "NGO needs 150 cooked vegetarian meals by 8 PM today."
    p3 = nlp_parser.parse_listing_text(t3)
    print(f"\n  Input: '{t3}'")
    print(f"  Result -> Qty: {p3['quantity']} {p3['unit']}, Deadline: {p3['deadline_display']}, Urgency: {p3['urgency_level']}")
    assert p3["quantity"] == 150.0 and "8:00 PM" in p3["deadline_display"]

    # 2. Test Surplus REST API
    print("\n[2] Testing Core Surplus REST APIs:")
    r_parse_surplus = client.post("/api/v1/surplus/parse", json={"raw_text": t1})
    print(f"  - POST /api/v1/surplus/parse -> Status {r_parse_surplus.status_code}")
    assert r_parse_surplus.status_code == 200

    r_create_surplus = client.post("/api/v1/surplus/", json={"raw_nlp_text": t1, "is_simulated": True})
    print(f"  - POST /api/v1/surplus/ -> Status {r_create_surplus.status_code}")
    assert r_create_surplus.status_code == 201
    surplus_id = r_create_surplus.json()["id"]

    r_get_surplus = client.get(f"/api/v1/surplus/{surplus_id}")
    print(f"  - GET /api/v1/surplus/{surplus_id} -> Status {r_get_surplus.status_code}")
    assert r_get_surplus.status_code == 200

    # 3. Test Demand REST API
    print("\n[3] Testing Core Demand REST APIs:")
    r_parse_demand = client.post("/api/v1/demand/parse", json={"raw_text": t3})
    print(f"  - POST /api/v1/demand/parse -> Status {r_parse_demand.status_code}")
    assert r_parse_demand.status_code == 200

    r_create_demand = client.post("/api/v1/demand/", json={"raw_nlp_text": t3, "is_simulated": True})
    print(f"  - POST /api/v1/demand/ -> Status {r_create_demand.status_code}")
    assert r_create_demand.status_code == 201
    demand_id = r_create_demand.json()["id"]

    r_get_demand = client.get(f"/api/v1/demand/{demand_id}")
    print(f"  - GET /api/v1/demand/{demand_id} -> Status {r_get_demand.status_code}")
    assert r_get_demand.status_code == 200

    # 4. Database Persistence Check
    print("\n[4] Database Persistence Check:")
    db = SessionLocal()
    try:
        s_db = db.query(SurplusListing).filter(SurplusListing.id == surplus_id).first()
        d_db = db.query(DemandListing).filter(DemandListing.id == demand_id).first()
        print(f"  - Surplus item '{s_db.title}' persisted in SQLite DB")
        print(f"  - Demand item '{d_db.title}' persisted in SQLite DB")
        assert s_db is not None and d_db is not None
    finally:
        db.close()

    print("\n" + "=" * 65)
    print("  >>> Phase 2A Final Verification PASSED! <<<")
    print("=" * 65)

if __name__ == "__main__":
    run_phase2a_runner()
