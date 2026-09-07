import os
import sys
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.ai.nlp_parser import nlp_parser, APP_TIMEZONE
from app.core.database import SessionLocal
from app.models.surplus import SurplusListing, StorageCondition
from app.models.demand import DemandListing, UrgencyLevel

client = TestClient(app)

# 1. Test complete surplus sentence with Asia/Kolkata timezone verification
def test_nlp_parser_complete_surplus_sentence():
    text = "We have 200 packed vegetarian meals available until 9 PM today. They need refrigeration."
    res = nlp_parser.parse_listing_text(text)
    assert res["quantity"] == 200.0
    assert res["unit"] == "meals"
    assert res["storage_condition"] == "REFRIGERATED"
    assert res["food_subtype"] == "vegetarian"
    assert res["resource_type"] == "Cooked Meals"
    assert res["confidence"] >= 0.7
    assert res["deadline_display"] is not None
    assert "9:00 PM" in res["deadline_display"]

# 2. Test Asia/Kolkata timezone deadline interpretation
def test_asia_kolkata_timezone_deadline_parsing():
    text = "NGO needs 100 cooked meals by 8 PM today."
    res = nlp_parser.parse_listing_text(text)
    assert res["deadline_display"] is not None
    assert "8:00 PM" in res["deadline_display"]
    
    # Verify parsing against current Asia/Kolkata datetime
    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    target_dt = datetime.fromisoformat(res["required_by"])
    assert target_dt.hour == 20
    assert target_dt.minute == 0
    # Date must be today or tomorrow IST
    assert target_dt.date() >= now_ist.date()

# 3. Test surplus sentence with missing storage information
def test_nlp_parser_missing_storage_information():
    text = "15 kg artisan sourdough bread loaves available for 24 hours."
    res = nlp_parser.parse_listing_text(text)
    assert res["quantity"] == 15.0
    assert res["unit"] == "kg"
    assert res["storage_condition"] is None # Does not hallucinate missing storage
    assert res["food_subtype"] == "bakery"
    assert res["perishability_hours"] == 24.0

# 4. Test demand sentence with urgency
def test_nlp_parser_demand_sentence_with_urgency():
    text = "NGO needs 150 cooked vegetarian meals by 8 PM today. Urgent high priority."
    res = nlp_parser.parse_listing_text(text)
    assert res["quantity"] == 150.0
    assert res["unit"] == "meals"
    assert res["food_subtype"] == "vegetarian"
    assert res["urgency_level"] == "HIGH"

# 5. Test quantity & unit extraction accuracy across various units
def test_nlp_parser_quantity_unit_extraction():
    res1 = nlp_parser.parse_listing_text("35.5 kg fresh produce")
    assert res1["quantity"] == 35.5
    assert res1["unit"] == "kg"

    res2 = nlp_parser.parse_listing_text("10 boxes of sourdough pastries")
    assert res2["quantity"] == 10.0
    assert res2["unit"] == "boxes"

# 6. Test invalid and empty input handling
def test_nlp_parser_invalid_empty_input():
    res_empty = nlp_parser.parse_listing_text("")
    assert res_empty["quantity"] is None
    assert res_empty["confidence"] == 0.0

    res_gibberish = nlp_parser.parse_listing_text("hello world random noise")
    assert res_gibberish["quantity"] is None

# 7. Test POST /api/v1/surplus/ API creation
def test_post_surplus_api_creation():
    payload = {
        "raw_nlp_text": "We have 45kg fresh produce surplus from morning banquet. Ambient storage.",
        "is_simulated": True
    }
    response = client.post("/api/v1/surplus/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["quantity"] == 45.0
    assert data["unit"] == "kg"
    assert data["storage_condition"] == "AMBIENT"
    assert "id" in data

# 8. Test POST /api/v1/demand/ API creation
def test_post_demand_api_creation():
    payload = {
        "raw_nlp_text": "Community shelter needs 60 cooked meals urgently by tonight.",
        "is_simulated": True
    }
    response = client.post("/api/v1/demand/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["requested_quantity"] == 60.0
    assert data["unit"] == "meals"
    assert data["urgency_level"] == "HIGH"
    assert "id" in data

# 9. Test GET endpoints (list and single item by ID)
def test_get_endpoints_and_single_item_lookup():
    res_surplus = client.get("/api/v1/surplus/")
    assert res_surplus.status_code == 200
    surplus_list = res_surplus.json()
    assert len(surplus_list) > 0

    first_surplus_id = surplus_list[0]["id"]
    res_single_surplus = client.get(f"/api/v1/surplus/{first_surplus_id}")
    assert res_single_surplus.status_code == 200
    assert res_single_surplus.json()["id"] == first_surplus_id

    res_demand = client.get("/api/v1/demand/")
    assert res_demand.status_code == 200
    demand_list = res_demand.json()
    assert len(demand_list) > 0

    first_demand_id = demand_list[0]["id"]
    res_single_demand = client.get(f"/api/v1/demand/{first_demand_id}")
    assert res_single_demand.status_code == 200
    assert res_single_demand.json()["id"] == first_demand_id

# 10. Test Data Persistence in SQLite Database
def test_database_persistence():
    payload = {
        "raw_nlp_text": "25 kg frozen vegetables available.",
        "is_simulated": True
    }
    res = client.post("/api/v1/surplus/", json=payload)
    assert res.status_code == 201
    item_id = res.json()["id"]

    db = SessionLocal()
    try:
        db_item = db.query(SurplusListing).filter(SurplusListing.id == item_id).first()
        assert db_item is not None
        assert db_item.quantity == 25.0
        assert db_item.storage_condition == StorageCondition.FROZEN
    finally:
        db.close()
