import os
import sys
import json
from datetime import datetime, timedelta

# Add backend directory to path so database models can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.core.database import SessionLocal, engine, Base
from app.models.organization import Organization, OrganizationType
from app.models.category import Category
from app.models.surplus import SurplusListing, StorageCondition, SurplusStatus
from app.models.demand import DemandListing, UrgencyLevel, DemandStatus
from app.models.allocation import Allocation
from app.models.impact import ImpactLog

def get_demo_target_time(target_hour, target_minute=0):
    """
    Generate target timestamp for TODAY at target_hour:target_minute.
    If current time has already passed target_hour today, roll forward to tomorrow
    so the demo record remains valid and non-expired whenever the script/app runs.
    """
    now = datetime.now()
    t = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if t <= now:
        t += timedelta(days=1)
    return t

def generate_mock_dataset():
    print("Initializing ReSource Mock Dataset Generator...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Clean up old/stale simulated records & allocations to keep demo state pristine
        db.query(ImpactLog).delete()
        db.query(Allocation).delete()
        db.query(SurplusListing).filter(SurplusListing.is_simulated == True).delete()
        db.query(DemandListing).filter(DemandListing.is_simulated == True).delete()
        db.commit()

        # 2. Seed Resource Categories
        categories_data = [
            {"name": "Cooked Meals", "default_unit": "kg"},
            {"name": "Food Surplus", "default_unit": "kg"},
            {"name": "Fresh Produce", "default_unit": "kg"},
            {"name": "Bakery Items", "default_unit": "kg"}
        ]
        
        category_map = {}
        for c_data in categories_data:
            existing = db.query(Category).filter(Category.name == c_data["name"]).first()
            if not existing:
                cat = Category(name=c_data["name"], default_unit=c_data["default_unit"])
                db.add(cat)
                db.flush()
                category_map[c_data["name"]] = cat
            else:
                category_map[c_data["name"]] = existing

        db.commit()

        # 3. Seed Supplier & Receiver Organizations (Simulated Data)
        suppliers_data = [
            {
                "name": "Grand Horizon Hotel",
                "org_type": OrganizationType.HOTEL,
                "address": "124 Central Boulevard",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "contact_email": "kitchen@grandhorizon.com",
                "contact_phone": "+1-555-0192"
            },
            {
                "name": "Bistro Verde Restaurant",
                "org_type": OrganizationType.RESTAURANT,
                "address": "45 Market Street",
                "latitude": 40.7180,
                "longitude": -74.0010,
                "contact_email": "surplus@bistroverde.com",
                "contact_phone": "+1-555-0144"
            },
            {
                "name": "Metropolitan Event Center",
                "org_type": OrganizationType.EVENT_VENUE,
                "address": "88 Convention Way",
                "latitude": 40.7250,
                "longitude": -74.0120,
                "contact_email": "events@metrocenter.com",
                "contact_phone": "+1-555-0188"
            }
        ]

        receivers_data = [
            {
                "name": "Hope Community Shelter",
                "org_type": OrganizationType.COMMUNITY_SHELTER,
                "address": "12 Shelter Lane",
                "latitude": 40.7150,
                "longitude": -73.9980,
                "contact_email": "intake@hopeshelter.org",
                "contact_phone": "+1-555-0211"
            },
            {
                "name": "Metro Food Bank NGO",
                "org_type": OrganizationType.FOOD_BANK,
                "address": "300 Relief Avenue",
                "latitude": 40.7300,
                "longitude": -73.9900,
                "contact_email": "operations@metrofoodbank.org",
                "contact_phone": "+1-555-0299"
            }
        ]

        suppliers = []
        for s_data in suppliers_data:
            existing = db.query(Organization).filter(Organization.name == s_data["name"]).first()
            if not existing:
                org = Organization(**s_data, is_verified=True)
                db.add(org)
                db.flush()
                suppliers.append(org)
            else:
                suppliers.append(existing)

        receivers = []
        for r_data in receivers_data:
            existing = db.query(Organization).filter(Organization.name == r_data["name"]).first()
            if not existing:
                org = Organization(**r_data, is_verified=True)
                db.add(org)
                db.flush()
                receivers.append(org)
            else:
                receivers.append(existing)

        db.commit()

        # 4. Seed Surplus Listings (SIMULATED DATA - Current & Non-Expired)
        now = datetime.now()
        cooked_cat = category_map["Cooked Meals"]
        bakery_cat = category_map["Bakery Items"]
        produce_cat = category_map["Fresh Produce"]

        expiry_9pm = get_demo_target_time(21, 0)

        surplus_samples = [
            {
                "supplier_id": suppliers[0].id, # Grand Horizon Hotel
                "category_id": cooked_cat.id,
                "title": "Buffet Dinner Surplus - Cooked Meals",
                "raw_nlp_text": "Grand Horizon Hotel has 350 kg of cooked meals left from today's corporate event. The food is freshly prepared, vegetarian, packed in food-grade containers, must be refrigerated, and can be safely distributed until 9:00 PM today.",
                "quantity": 350.0,
                "remaining_quantity": 350.0,
                "unit": "kg",
                "perishability_hours": 12.0,
                "storage_condition": StorageCondition.REFRIGERATED,
                "available_from": now,
                "expires_at": expiry_9pm,
                "status": SurplusStatus.AVAILABLE,
                "is_simulated": True
            },
            {
                "supplier_id": suppliers[1].id, # Bistro Verde Restaurant
                "category_id": bakery_cat.id,
                "title": "Fresh Artisan Bread & Pastries",
                "raw_nlp_text": "15kg assortment of sourdough loaves and fresh pastries baked today. Ambient storage.",
                "quantity": 15.0,
                "remaining_quantity": 15.0,
                "unit": "kg",
                "perishability_hours": 24.0,
                "storage_condition": StorageCondition.AMBIENT,
                "available_from": now,
                "expires_at": now + timedelta(hours=24),
                "status": SurplusStatus.AVAILABLE,
                "is_simulated": True
            }
        ]

        for surp in surplus_samples:
            s_item = SurplusListing(**surp)
            db.add(s_item)

        # 5. Seed Demand Listings (SIMULATED DATA - Current & Non-Expired)
        required_8pm = get_demo_target_time(20, 0)

        demand_samples = [
            {
                "receiver_id": receivers[0].id, # Hope Community Shelter
                "category_id": cooked_cat.id,
                "title": "Evening Dinner Service - Hope Community Shelter",
                "raw_nlp_text": "Hope Community Shelter needs 180 kg of cooked meals for tonight's dinner service for families staying at the shelter. The meals are required by 8:00 PM today, should arrive refrigerated, and this is a high-priority request.",
                "requested_quantity": 180.0,
                "fulfilled_quantity": 0.0,
                "unit": "kg",
                "urgency_level": UrgencyLevel.HIGH,
                "storage_capacity": "REFRIGERATED",
                "required_by": required_8pm,
                "status": DemandStatus.OPEN,
                "is_simulated": True
            },
            {
                "receiver_id": receivers[1].id, # Metro Food Bank NGO
                "category_id": produce_cat.id,
                "title": "Fresh Produce Request for Weekly Food Parcels",
                "raw_nlp_text": "Requesting 50kg fresh fruits or vegetables for family emergency distribution hampers.",
                "requested_quantity": 50.0,
                "fulfilled_quantity": 0.0,
                "unit": "kg",
                "urgency_level": UrgencyLevel.MEDIUM,
                "storage_capacity": "AMBIENT",
                "required_by": now + timedelta(days=2),
                "status": DemandStatus.OPEN,
                "is_simulated": True
            }
        ]

        for dem in demand_samples:
            d_item = DemandListing(**dem)
            db.add(d_item)

        db.commit()
        print("Database successfully populated with current non-expired demo data!")

        # 6. Export JSON Sample Artifacts in data/
        data_dir = os.path.dirname(__file__)
        with open(os.path.join(data_dir, "sample_food_surplus.json"), "w") as f:
            json.dump([
                {
                    "id": "simulated-surplus-001",
                    "supplier": "Grand Horizon Hotel",
                    "title": "Buffet Dinner Surplus - Cooked Meals",
                    "quantity_kg": 350.0,
                    "perishability_hours": 12.0,
                    "storage": "REFRIGERATED",
                    "expires_at": expiry_9pm.isoformat(),
                    "is_simulated": True
                },
                {
                    "id": "simulated-surplus-002",
                    "supplier": "Bistro Verde Restaurant",
                    "title": "Fresh Artisan Bread & Pastries",
                    "quantity_kg": 15.0,
                    "perishability_hours": 24.0,
                    "storage": "AMBIENT",
                    "expires_at": (now + timedelta(hours=24)).isoformat(),
                    "is_simulated": True
                }
            ], f, indent=2)

        with open(os.path.join(data_dir, "sample_ngo_demands.json"), "w") as f:
            json.dump([
                {
                    "id": "simulated-demand-001",
                    "receiver": "Hope Community Shelter",
                    "title": "Evening Dinner Service - Hope Community Shelter",
                    "requested_quantity_kg": 180.0,
                    "urgency": "HIGH",
                    "required_by": required_8pm.isoformat(),
                    "storage_capacity": "REFRIGERATED",
                    "is_simulated": True
                },
                {
                    "id": "simulated-demand-002",
                    "receiver": "Metro Food Bank NGO",
                    "title": "Fresh Produce Request for Weekly Food Parcels",
                    "requested_quantity_kg": 50.0,
                    "urgency": "MEDIUM",
                    "required_by": (now + timedelta(days=2)).isoformat(),
                    "storage_capacity": "AMBIENT",
                    "is_simulated": True
                }
            ], f, indent=2)

        print("Exported updated data/sample_food_surplus.json and data/sample_ngo_demands.json.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding mock dataset: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_mock_dataset()
