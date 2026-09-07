import os
import sys
import json

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal
from app.models.organization import Organization
from app.models.surplus import SurplusListing
from app.models.demand import DemandListing
from app.models.category import Category

def run_phase1_verification():
    print("=" * 60)
    print("      ReSource HG - Phase 1 Sample Verification Suite")
    print("=" * 60)
    
    # 1. Database Entity Verification
    db = SessionLocal()
    try:
        categories_count = db.query(Category).count()
        orgs_count = db.query(Organization).count()
        surplus_count = db.query(SurplusListing).count()
        demand_count = db.query(DemandListing).count()
        
        print("\n[1] Database Entities Status:")
        print(f"  - Resource Categories: {categories_count}")
        print(f"  - Organizations: {orgs_count}")
        print(f"  - Surplus Listings: {surplus_count}")
        print(f"  - Demand Listings: {demand_count}")
        
        # Verify is_simulated flag compliance
        simulated_surplus = db.query(SurplusListing).filter(SurplusListing.is_simulated == True).count()
        simulated_demands = db.query(DemandListing).filter(DemandListing.is_simulated == True).count()
        print(f"  - Simulated Surplus Listings: {simulated_surplus}/{surplus_count}")
        print(f"  - Simulated Demand Listings: {simulated_demands}/{demand_count}")
        assert simulated_surplus > 0, "No simulated surplus listings found!"
        assert simulated_demands > 0, "No simulated demand listings found!"
        
    finally:
        db.close()
        
    # 2. JSON Sample Export Verification
    data_dir = os.path.dirname(__file__)
    surplus_json_path = os.path.join(data_dir, "sample_food_surplus.json")
    demand_json_path = os.path.join(data_dir, "sample_ngo_demands.json")
    
    print("\n[2] JSON Artifacts Verification:")
    if os.path.exists(surplus_json_path):
        with open(surplus_json_path, "r") as f:
            surplus_json = json.load(f)
            print(f"  - sample_food_surplus.json: {len(surplus_json)} items found")
    else:
        print("  - sample_food_surplus.json: MISSING")
        
    if os.path.exists(demand_json_path):
        with open(demand_json_path, "r") as f:
            demand_json = json.load(f)
            print(f"  - sample_ngo_demands.json: {len(demand_json)} items found")
    else:
        print("  - sample_ngo_demands.json: MISSING")

    # 3. FastAPI REST API Endpoint Verification
    print("\n[3] FastAPI Endpoint Integration Tests:")
    client = TestClient(app)
    
    # Test Health Endpoint
    res_health = client.get("/api/v1/health")
    print(f"  - GET /api/v1/health -> Status {res_health.status_code}")
    print(f"    Payload: {res_health.json()}")
    assert res_health.status_code == 200
    
    # Test Organizations Endpoint
    res_orgs = client.get("/api/v1/organizations/")
    print(f"  - GET /api/v1/organizations/ -> Status {res_orgs.status_code} ({len(res_orgs.json())} orgs)")
    assert res_orgs.status_code == 200

    # Test Surplus Endpoint
    res_surplus = client.get("/api/v1/surplus/")
    print(f"  - GET /api/v1/surplus/ -> Status {res_surplus.status_code} ({len(res_surplus.json())} listings)")
    assert res_surplus.status_code == 200

    # Test Demand Endpoint
    res_demand = client.get("/api/v1/demand/")
    print(f"  - GET /api/v1/demand/ -> Status {res_demand.status_code} ({len(res_demand.json())} demands)")
    assert res_demand.status_code == 200

    print("\n" + "=" * 60)
    print("  >>> Phase 1 Sample Execution & Verification PASSED! <<<")
    print("=" * 60)

if __name__ == "__main__":
    run_phase1_verification()
