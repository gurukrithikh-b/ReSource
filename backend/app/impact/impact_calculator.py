"""
Phase 5 — Sustainability Impact Intelligence Calculator
======================================================
Deterministic impact calculation engine converting successful resource allocations
into defensible social and environmental impact metrics.

Impact Formulas & Baseline Assumptions:
---------------------------------------
1. Resource/Food Rescued:
   quantity_kg = allocated_quantity (in kg)

2. Demand Fulfilled:
   demand_fulfilled_kg = allocated_quantity (in kg)

3. Estimated Meals Served:
   meals_served = quantity_kg / 0.4 (standard 0.4 kg / meal assumption = 2.5 meals per kg)

4. Estimated CO2 Avoided (kg CO2e):
   co2_avoided_kg = quantity_kg * category_co2_factor
   Category Factors (kg CO2e avoided per kg rescued):
   - Prepared / Cooked Meals: 2.5 kg CO2e / kg
   - Fresh Produce / Vegetables: 1.9 kg CO2e / kg
   - Bakery / Bread: 1.2 kg CO2e / kg
   - Dairy Products: 3.2 kg CO2e / kg
   - Meat / Protein: 6.5 kg CO2e / kg
   - Default Fallback: 2.5 kg CO2e / kg

5. Community Impact:
   Count of unique receiving community partners receiving allocations.

Idempotency:
------------
Prevents double-counting by verifying existing ImpactLog records for the same allocation ID.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.impact import ImpactLog
from app.models.allocation import Allocation
from app.models.surplus import SurplusListing
from app.models.demand import DemandListing
from app.models.organization import Organization


class ImpactCalculator:
    def __init__(self):
        # Standard conversion: 0.4 kg per meal (2.5 meals / kg)
        self.MEAL_CONVERSION_KG = 0.4

        # Category CO2e avoidance factors (kg CO2e saved per kg food waste avoided)
        self.CATEGORY_CO2_FACTORS: Dict[str, float] = {
            "cooked meals": 2.5,
            "prepared food": 2.5,
            "meals": 2.5,
            "fresh produce": 1.9,
            "produce": 1.9,
            "fruits": 1.9,
            "vegetables": 1.9,
            "bakery items": 1.2,
            "bakery": 1.2,
            "bread": 1.2,
            "dairy": 3.2,
            "dairy products": 3.2,
            "meat": 6.5,
            "protein": 6.5,
            "food surplus": 2.5,
        }
        self.DEFAULT_CO2_FACTOR = 2.5

    def get_category_co2_factor(self, category_name: Optional[str]) -> float:
        """Return the category-specific CO2 factor or default fallback."""
        if not category_name:
            return self.DEFAULT_CO2_FACTOR
        key = category_name.strip().lower()
        return self.CATEGORY_CO2_FACTORS.get(key, self.DEFAULT_CO2_FACTOR)

    def calculate_metrics(
        self,
        quantity_kg: float,
        category_name: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Deterministic calculation of impact metrics for a given quantity (kg) and category.
        """
        qty = max(0.0, float(quantity_kg or 0.0))
        co2_factor = self.get_category_co2_factor(category_name)
        
        meals_estimate = round(qty / self.MEAL_CONVERSION_KG, 1)
        co2_avoided = round(qty * co2_factor, 2)
        
        return {
            "resource_recovered_kg": qty,
            "demand_fulfilled_kg": qty,
            "meals_provided_estimate": meals_estimate,
            "co2_avoided_kg": co2_avoided,
            "co2_factor_used": co2_factor,
        }

    def process_allocation_impact(
        self,
        db: Session,
        allocation_id: str,
        allocated_quantity: float,
        category_name: Optional[str] = None,
        supplier_id: Optional[str] = None,
        supplier_name: Optional[str] = None,
        receiver_id: Optional[str] = None,
        receiver_name: Optional[str] = None,
    ) -> ImpactLog:
        """
        Calculate and store an ImpactLog for a single allocation in an idempotent manner.
        """
        # Idempotency check: look for existing record for allocation_id
        if allocation_id:
            existing = db.query(ImpactLog).filter(ImpactLog.allocation_id == allocation_id).first()
            if existing:
                # Update existing metrics if quantity changed
                metrics = self.calculate_metrics(allocated_quantity, category_name or existing.category)
                existing.resource_recovered_kg = metrics["resource_recovered_kg"]
                existing.demand_fulfilled_kg = metrics["demand_fulfilled_kg"]
                existing.meals_provided_estimate = metrics["meals_provided_estimate"]
                existing.co2_avoided_kg = metrics["co2_avoided_kg"]
                if category_name:
                    existing.category = category_name
                if supplier_name:
                    existing.supplier_name = supplier_name
                if receiver_name:
                    existing.receiver_name = receiver_name
                db.commit()
                db.refresh(existing)
                return existing

        metrics = self.calculate_metrics(allocated_quantity, category_name)

        impact_record = ImpactLog(
            allocation_id=allocation_id,
            resource_recovered_kg=metrics["resource_recovered_kg"],
            demand_fulfilled_kg=metrics["demand_fulfilled_kg"],
            meals_provided_estimate=metrics["meals_provided_estimate"],
            co2_avoided_kg=metrics["co2_avoided_kg"],
            category=category_name or "Food Surplus",
            supplier_id=supplier_id,
            supplier_name=supplier_name or "Resource Provider",
            receiver_id=receiver_id,
            receiver_name=receiver_name or "Community Partner",
            calculated_at=datetime.utcnow(),
        )

        db.add(impact_record)
        db.commit()
        db.refresh(impact_record)
        return impact_record

    def process_batch_allocations(
        self,
        db: Session,
        allocations: List[Any]
    ) -> List[ImpactLog]:
        """
        Process a list of allocation schemas/models and create/update ImpactLog records idempotently.
        """
        results: List[ImpactLog] = []
        for alloc in allocations:
            if isinstance(alloc, dict):
                alloc_id = alloc.get("allocation_id") or alloc.get("id") or f"{alloc.get('surplus_id') or 'surplus'}_{alloc.get('demand_id') or 'demand'}"
                qty = alloc.get("allocated_quantity", 0.0)
                cat_name = alloc.get("category_name")
                sup_name = alloc.get("supplier_name")
                rec_name = alloc.get("receiver_name")
                sup_id = alloc.get("supplier_id")
                rec_id = alloc.get("receiver_id")
            else:
                alloc_id = (
                    getattr(alloc, "allocation_id", None)
                    or getattr(alloc, "id", None)
                    or f"{getattr(alloc, 'surplus_id', None) or 'surplus'}_{getattr(alloc, 'demand_id', None) or 'demand'}"
                )
                qty = getattr(alloc, "allocated_quantity", 0.0)
                cat_name = getattr(alloc, "category_name", None)
                sup_name = getattr(alloc, "supplier_name", None)
                rec_name = getattr(alloc, "receiver_name", None)
                sup_id = getattr(alloc, "supplier_id", None)
                rec_id = getattr(alloc, "receiver_id", None)

            record = self.process_allocation_impact(
                db=db,
                allocation_id=str(alloc_id),
                allocated_quantity=float(qty),
                category_name=cat_name,
                supplier_id=sup_id,
                supplier_name=sup_name,
                receiver_id=rec_id,
                receiver_name=rec_name,
            )
            results.append(record)
        return results


impact_calculator = ImpactCalculator()
