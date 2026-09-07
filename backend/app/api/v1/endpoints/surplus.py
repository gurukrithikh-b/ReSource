from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.models.surplus import SurplusListing, StorageCondition, SurplusStatus
from app.models.organization import Organization, OrganizationType
from app.models.category import Category
from app.schemas.surplus import SurplusListingCreate, SurplusListingResponse
from app.schemas.nlp import ParseIntakeRequest, ParsedIntakeResponse
from app.ai.nlp_parser import nlp_parser

router = APIRouter()

@router.post("/parse", response_model=ParsedIntakeResponse)
def parse_surplus_intake(request: ParseIntakeRequest):
    """
    NLP Parse Preview Endpoint:
    Accepts natural language text and returns structured parsed entity fields without saving to DB.
    """
    if not request.raw_text or not request.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Raw natural language text input cannot be empty."
        )
    parsed_data = nlp_parser.parse_listing_text(request.raw_text)
    return parsed_data

@router.get("/", response_model=List[SurplusListingResponse])
def list_surplus(db: Session = Depends(get_db)):
    """List all available surplus listings."""
    return db.query(SurplusListing).order_by(SurplusListing.created_at.desc()).all()

@router.get("/{surplus_id}", response_model=SurplusListingResponse)
def get_surplus_by_id(surplus_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a single surplus listing by ID."""
    listing = db.query(SurplusListing).filter(SurplusListing.id == surplus_id).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Surplus listing with ID '{surplus_id}' not found."
        )
    return listing

@router.post("/", response_model=SurplusListingResponse, status_code=status.HTTP_201_CREATED)
def create_surplus(surplus_in: SurplusListingCreate, db: Session = Depends(get_db)):
    """
    Create a new surplus listing.
    Supports either pre-structured fields or unstructured natural language note (`raw_nlp_text`),
    auto-extracting missing entity values via the NLP parser.
    """
    parsed = {}
    if surplus_in.raw_nlp_text:
        parsed = nlp_parser.parse_listing_text(surplus_in.raw_nlp_text)

    # 1. Resolve Supplier ID
    supplier_id = surplus_in.supplier_id
    if not supplier_id:
        supplier_org = db.query(Organization).filter(
            Organization.org_type.in_([OrganizationType.HOTEL, OrganizationType.RESTAURANT, OrganizationType.EVENT_VENUE])
        ).first()
        if not supplier_org:
            supplier_org = db.query(Organization).first()
        if not supplier_org:
            supplier_org = Organization(
                name="Grand Horizon Hotel",
                org_type=OrganizationType.HOTEL,
                address="123 Main St, Central District",
                latitude=12.9716,
                longitude=77.5946
            )
            db.add(supplier_org)
            db.flush()
        supplier_id = supplier_org.id

    # 2. Resolve Category ID
    category_id = surplus_in.category_id
    if not category_id:
        res_type = parsed.get("resource_type", "Cooked Meals")
        cat = db.query(Category).filter(Category.name.ilike(f"%{res_type}%")).first()
        if not cat:
            cat = db.query(Category).first()
        if not cat:
            # Fallback inline category creation
            cat = Category(name=res_type, default_unit="kg")
            db.add(cat)
            db.flush()
        category_id = cat.id

    # 3. Resolve Quantity & Validation
    quantity = surplus_in.quantity if surplus_in.quantity is not None else parsed.get("quantity")
    if quantity is None or quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be a positive number (> 0). Could not extract valid quantity from input."
        )

    # 4. Resolve Unit
    unit = surplus_in.unit or parsed.get("unit") or "kg"

    # 5. Resolve Storage Condition
    storage = surplus_in.storage_condition
    if not storage:
        ext_storage = parsed.get("storage_condition")
        if ext_storage and ext_storage in StorageCondition.__members__:
            storage = StorageCondition[ext_storage]
        else:
            storage = StorageCondition.AMBIENT

    # 6. Resolve Perishability & Expiry
    perishability_hours = surplus_in.perishability_hours if surplus_in.perishability_hours is not None else parsed.get("perishability_hours")
    if perishability_hours is None or perishability_hours <= 0:
        perishability_hours = 12.0

    now = datetime.now(timezone.utc)
    expires_at = surplus_in.expires_at
    if not expires_at:
        parsed_exp = parsed.get("expires_at")
        if parsed_exp:
            try:
                expires_at = datetime.fromisoformat(parsed_exp)
            except Exception:
                expires_at = now + timedelta(hours=perishability_hours)
        else:
            expires_at = now + timedelta(hours=perishability_hours)

    # 7. Title Generation
    title = surplus_in.title
    if not title:
        subtype = (parsed.get("food_subtype") or "Food Surplus").title()
        title = f"{subtype} ({quantity} {unit})"

    db_surplus = SurplusListing(
        supplier_id=supplier_id,
        category_id=category_id,
        title=title,
        raw_nlp_text=surplus_in.raw_nlp_text,
        quantity=quantity,
        remaining_quantity=quantity,
        unit=unit,
        perishability_hours=perishability_hours,
        storage_condition=storage,
        available_from=surplus_in.available_from or now,
        expires_at=expires_at,
        status=SurplusStatus.AVAILABLE,
        is_simulated=surplus_in.is_simulated
    )

    db.add(db_surplus)
    db.commit()
    db.refresh(db_surplus)
    return db_surplus
