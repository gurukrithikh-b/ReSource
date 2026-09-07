from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.demand import DemandListing, UrgencyLevel, DemandStatus
from app.models.organization import Organization, OrganizationType
from app.models.category import Category
from app.schemas.demand import DemandListingCreate, DemandListingResponse
from app.schemas.nlp import ParseIntakeRequest, ParsedIntakeResponse
from app.ai.nlp_parser import nlp_parser

router = APIRouter()

@router.post("/parse", response_model=ParsedIntakeResponse)
def parse_demand_intake(request: ParseIntakeRequest):
    """
    NLP Parse Preview Endpoint:
    Accepts natural language text and returns structured parsed entity fields for demand preview without saving to DB.
    """
    if not request.raw_text or not request.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raw natural language text input cannot be empty."
        )
    parsed_data = nlp_parser.parse_listing_text(request.raw_text)
    return parsed_data

@router.get("/", response_model=List[DemandListingResponse])
def list_demands(db: Session = Depends(get_db)):
    """List all open demand listings."""
    return db.query(DemandListing).order_by(DemandListing.created_at.desc()).all()

@router.get("/{demand_id}", response_model=DemandListingResponse)
def get_demand_by_id(demand_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a single demand listing by ID."""
    listing = db.query(DemandListing).filter(DemandListing.id == demand_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demand listing with ID '{demand_id}' not found."
        )
    return listing

@router.post("/", response_model=DemandListingResponse, status_code=status.HTTP_201_CREATED)
def create_demand(demand_in: DemandListingCreate, db: Session = Depends(get_db)):
    """
    Create a new demand listing.
    Supports either pre-structured fields or unstructured natural language demand notes (`raw_nlp_text`),
    auto-extracting missing entity values via the NLP parser.
    """
    parsed = {}
    if demand_in.raw_nlp_text:
        parsed = nlp_parser.parse_listing_text(demand_in.raw_nlp_text)

    # 1. Resolve Receiver ID
    receiver_id = demand_in.receiver_id
    if not receiver_id:
        receiver_org = db.query(Organization).filter(
            Organization.org_type.in_([OrganizationType.COMMUNITY_SHELTER, OrganizationType.FOOD_BANK])
        ).first()
        if not receiver_org:
            receiver_org = db.query(Organization).first()
        if not receiver_org:
            receiver_org = Organization(
                name="Hope Shelter NGO",
                org_type=OrganizationType.COMMUNITY_SHELTER,
                address="45 Community Ave",
                latitude=12.9600,
                longitude=77.6000
            )
            db.add(receiver_org)
            db.flush()
        receiver_id = receiver_org.id

    # 2. Resolve Category ID
    category_id = demand_in.category_id
    if not category_id:
        res_type = parsed.get("resource_type", "Cooked Meals")
        cat = db.query(Category).filter(Category.name.ilike(f"%{res_type}%")).first()
        if not cat:
            cat = db.query(Category).first()
        if not cat:
            cat = Category(name=res_type, default_unit="kg")
            db.add(cat)
            db.flush()
        category_id = cat.id

    # 3. Resolve Requested Quantity & Validation
    requested_quantity = demand_in.requested_quantity if demand_in.requested_quantity is not None else parsed.get("quantity")
    if requested_quantity is None or requested_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity must be a positive number (> 0). Could not extract valid quantity from input."
        )

    # 4. Resolve Unit
    unit = demand_in.unit or parsed.get("unit") or "kg"

    # 5. Resolve Urgency Level
    urgency = demand_in.urgency_level
    if not urgency:
        ext_urg = parsed.get("urgency_level")
        if ext_urg and ext_urg in UrgencyLevel.__members__:
            urgency = UrgencyLevel[ext_urg]
        else:
            urgency = UrgencyLevel.MEDIUM

    # 6. Resolve Storage Capacity
    storage_capacity = demand_in.storage_capacity or parsed.get("storage_condition") or "AMBIENT"

    # 7. Resolve Required By Timeframe
    now = datetime.now(timezone.utc)
    required_by = demand_in.required_by
    if not required_by:
        parsed_req = parsed.get("required_by")
        if parsed_req:
            try:
                required_by = datetime.fromisoformat(parsed_req)
            except Exception:
                required_by = now + timedelta(hours=24)
        else:
            required_by = now + timedelta(hours=24)

    # 8. Title Generation
    title = demand_in.title
    if not title:
        subtype = (parsed.get("food_subtype") or "Food Request").title()
        title = f"{subtype} Demand ({requested_quantity} {unit})"

    db_demand = DemandListing(
        receiver_id=receiver_id,
        category_id=category_id,
        title=title,
        raw_nlp_text=demand_in.raw_nlp_text,
        requested_quantity=requested_quantity,
        fulfilled_quantity=0.0,
        unit=unit,
        urgency_level=urgency,
        storage_capacity=storage_capacity,
        required_by=required_by,
        status=DemandStatus.OPEN,
        is_simulated=demand_in.is_simulated
    )

    db.add(db_demand)
    db.commit()
    db.refresh(db_demand)
    return db_demand
