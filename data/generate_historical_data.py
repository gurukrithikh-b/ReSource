"""
generate_historical_data.py
───────────────────────────────────────────────────────────────────────────────
ReSource Phase 3.1 — Historical Data Foundation
───────────────────────────────────────────────────────────────────────────────

PURPOSE
    Generates clearly-labelled synthetic historical records covering
    approximately 12 months of daily activity across multiple supplier and
    receiver organisations.  These records will be used later (Phase 3.2+) to
    develop and validate the ReSource ML prediction models.

DISCLAIMER
    ALL data produced by this script is SYNTHETIC / SIMULATED.
    is_simulated = True on every single row.
    None of this represents real-world organisations, transactions, or events.

OUTPUT
    data/historical_surplus.csv
    data/historical_demand.csv

DESIGN NOTES
    Categories and organisation types follow the existing ReSource database
    schema (surplus.py, demand.py, category.py, organisation.py) so that the
    CSVs can be cross-referenced against live DB records without schema
    conflicts.

    Realistic patterns deliberately embedded:
      * Weekday / weekend quantity differences per category
      * Recurring per-organisation behaviour profiles (volume scale, preferred
        category, storage, typical urgency)
      * Category-specific baseline quantity ranges and perishability windows
      * High-volume event spikes (bank-holiday weeks, quarterly events)
      * Gaussian noise on every quantity so the distributions are not flat
      * Gradual seasonal drift (surplus dips in summer, spikes in winter)
      * Demand is correlated with supply but independently noisy, with
        additional end-of-month peaks (distribution / charity runs)
"""

import os
import random
import math
import csv
import calendar
from datetime import date, timedelta

# ─── Reproducibility ─────────────────────────────────────────────────────────
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ─── Date Range: 12 months of daily data ──────────────────────────────────────
START_DATE = date(2025, 1, 1)
END_DATE   = date(2025, 12, 31)   # inclusive

# ─── Categories (aligned with generate_mock_data.py / category model) ─────────
# Each entry: (category_name, default_unit, baseline_qty_range,
#              perishability_hours_range, storage_condition)
CATEGORIES = [
    {
        "name": "Cooked Meals",
        "unit": "kg",
        "qty_range": (10, 80),
        "perish_range": (4, 12),
        "storage": "REFRIGERATED",
        "weekend_factor": 1.4,   # more cooked meals on weekends (events/brunches)
        "summer_factor": 0.85,
    },
    {
        "name": "Fresh Produce",
        "unit": "kg",
        "qty_range": (20, 120),
        "perish_range": (24, 72),
        "storage": "AMBIENT",
        "weekend_factor": 1.1,
        "summer_factor": 1.25,   # seasonal abundance
    },
    {
        "name": "Bakery Items",
        "unit": "kg",
        "qty_range": (5, 40),
        "perish_range": (12, 36),
        "storage": "AMBIENT",
        "weekend_factor": 1.3,
        "summer_factor": 0.95,
    },
    {
        "name": "Food Surplus",  # generic/mixed surplus category
        "unit": "kg",
        "qty_range": (15, 100),
        "perish_range": (8, 48),
        "storage": "AMBIENT",
        "weekend_factor": 1.2,
        "summer_factor": 1.0,
    },
]

# ─── Supplier Organisations (aligned with organisation model / mock data) ──────
# Each entry includes a stable org_id so CSVs can be cross-referenced,
# a preferred category mix, a volume scale, and a typical storage condition.
SUPPLIERS = [
    {
        "name": "Grand Horizon Hotel",
        "org_id": "hist-sup-001",
        "org_type": "HOTEL",
        "preferred_categories": ["Cooked Meals", "Food Surplus"],
        "volume_scale": 1.6,      # high-volume establishment
        "base_listings_per_day": 1.3,
    },
    {
        "name": "Bistro Verde Restaurant",
        "org_id": "hist-sup-002",
        "org_type": "RESTAURANT",
        "preferred_categories": ["Cooked Meals", "Bakery Items"],
        "volume_scale": 0.8,
        "base_listings_per_day": 0.9,
    },
    {
        "name": "Metropolitan Event Center",
        "org_id": "hist-sup-003",
        "org_type": "EVENT_VENUE",
        "preferred_categories": ["Food Surplus", "Cooked Meals"],
        "volume_scale": 2.0,      # very high on event days
        "base_listings_per_day": 0.6,  # fewer days active (only event days)
    },
    {
        "name": "Sunrise University Canteen",
        "org_id": "hist-sup-004",
        "org_type": "INSTITUTION",
        "preferred_categories": ["Cooked Meals", "Fresh Produce"],
        "volume_scale": 1.1,
        "base_listings_per_day": 1.0,
    },
    {
        "name": "Harvest Organic Market",
        "org_id": "hist-sup-005",
        "org_type": "INSTITUTION",
        "preferred_categories": ["Fresh Produce", "Bakery Items"],
        "volume_scale": 0.9,
        "base_listings_per_day": 1.2,
    },
    {
        "name": "The Riverside Hotel",
        "org_id": "hist-sup-006",
        "org_type": "HOTEL",
        "preferred_categories": ["Cooked Meals", "Bakery Items", "Food Surplus"],
        "volume_scale": 1.3,
        "base_listings_per_day": 1.1,
    },
]

# ─── Receiver Organisations ────────────────────────────────────────────────────
RECEIVERS = [
    {
        "name": "Hope Community Shelter",
        "org_id": "hist-rec-001",
        "org_type": "COMMUNITY_SHELTER",
        "preferred_categories": ["Cooked Meals", "Food Surplus"],
        "need_scale": 1.0,
        "typical_urgency_weights": {"LOW": 5, "MEDIUM": 30, "HIGH": 50, "CRITICAL": 15},
    },
    {
        "name": "Metro Food Bank NGO",
        "org_id": "hist-rec-002",
        "org_type": "FOOD_BANK",
        "preferred_categories": ["Fresh Produce", "Food Surplus", "Bakery Items"],
        "need_scale": 1.4,
        "typical_urgency_weights": {"LOW": 10, "MEDIUM": 45, "HIGH": 35, "CRITICAL": 10},
    },
    {
        "name": "City Bridge Women's NGO",
        "org_id": "hist-rec-003",
        "org_type": "NGO",
        "preferred_categories": ["Cooked Meals", "Bakery Items"],
        "need_scale": 0.7,
        "typical_urgency_weights": {"LOW": 15, "MEDIUM": 40, "HIGH": 35, "CRITICAL": 10},
    },
    {
        "name": "Sunrise Youth Foundation",
        "org_id": "hist-rec-004",
        "org_type": "NGO",
        "preferred_categories": ["Fresh Produce", "Cooked Meals"],
        "need_scale": 0.8,
        "typical_urgency_weights": {"LOW": 20, "MEDIUM": 45, "HIGH": 30, "CRITICAL": 5},
    },
    {
        "name": "Riverside Community Shelter",
        "org_id": "hist-rec-005",
        "org_type": "COMMUNITY_SHELTER",
        "preferred_categories": ["Food Surplus", "Cooked Meals"],
        "need_scale": 1.1,
        "typical_urgency_weights": {"LOW": 5, "MEDIUM": 25, "HIGH": 55, "CRITICAL": 15},
    },
]

# ─── Category lookup for fast access ──────────────────────────────────────────
CAT_MAP = {c["name"]: c for c in CATEGORIES}

# ─── Helper: pick from weighted dict ──────────────────────────────────────────
def weighted_choice(weight_dict):
    keys = list(weight_dict.keys())
    weights = list(weight_dict.values())
    return random.choices(keys, weights=weights, k=1)[0]


# ─── Helper: seasonal factor ───────────────────────────────────────────────────
def seasonal_factor(d, cat_name):
    """Return a multiplier (~0.7-1.3) based on month and category."""
    month = d.month
    # Simple sinusoidal seasonal curve: peak in Jan/Dec, trough in July.
    base_seasonal = 1.0 + 0.15 * math.cos(2 * math.pi * (month - 1) / 12)
    cat = CAT_MAP.get(cat_name, {})
    summer_adj = cat.get("summer_factor", 1.0)
    # summer_adj applied around July
    summer_intensity = max(0, math.cos(2 * math.pi * (month - 7) / 12))
    return base_seasonal * (1.0 + (summer_adj - 1.0) * summer_intensity)


# ─── Helper: weekend factor per category ──────────────────────────────────────
def weekend_factor(d, cat_name):
    cat = CAT_MAP.get(cat_name, {})
    if d.weekday() >= 5:          # Saturday=5, Sunday=6
        return cat.get("weekend_factor", 1.0)
    return 1.0


# ─── Helper: event spike indicator ────────────────────────────────────────────
EVENT_WEEKS = {
    (1, 1), (3, 4), (5, 4), (7, 1), (8, 3),
    (10, 4), (11, 4), (12, 3), (12, 4),
}

def is_event_day(d):
    week_of_month = (d.day - 1) // 7 + 1
    return (d.month, week_of_month) in EVENT_WEEKS


def event_spike_factor(d, org_type):
    """Event venues spike hard; others spike moderately."""
    if not is_event_day(d):
        return 1.0
    if org_type == "EVENT_VENUE":
        return random.uniform(1.8, 2.8)
    return random.uniform(1.1, 1.4)


# ─── Helper: end-of-month demand surge ────────────────────────────────────────
def end_of_month_factor(d):
    """Demand spikes in last 5 days of month (distribution/charity runs)."""
    last_day = calendar.monthrange(d.year, d.month)[1]
    if d.day >= last_day - 4:
        return random.uniform(1.2, 1.6)
    return 1.0


# ─── Helper: gaussian noise ───────────────────────────────────────────────────
def noisy(value, std_pct=0.15):
    """Add Gaussian noise; std_pct as fraction of value. Always positive."""
    noise = random.gauss(0, value * std_pct)
    return max(1.0, round(value + noise, 2))


# ─── Generate Surplus Records ─────────────────────────────────────────────────
def generate_surplus_records():
    records = []
    current = START_DATE
    while current <= END_DATE:
        for supplier in SUPPLIERS:
            # Probabilistically decide how many listings this supplier posts today
            avg_listings = supplier["base_listings_per_day"]
            # EVENT_VENUE rarely operates on weekdays without an event
            if supplier["org_type"] == "EVENT_VENUE" and not is_event_day(current):
                avg_listings *= 0.25
            # Institutions typically skip Sundays
            if supplier["org_type"] == "INSTITUTION" and current.weekday() == 6:
                avg_listings *= 0.15

            n_listings = 1 if random.random() < avg_listings else 0

            for _ in range(n_listings):
                cat_name = random.choice(supplier["preferred_categories"])
                cat = CAT_MAP[cat_name]

                # Quantity: baseline x volume_scale x seasonal x weekend x event x noise
                base_qty = random.uniform(*cat["qty_range"])
                qty = (
                    base_qty
                    * supplier["volume_scale"]
                    * seasonal_factor(current, cat_name)
                    * weekend_factor(current, cat_name)
                    * event_spike_factor(current, supplier["org_type"])
                )
                qty = noisy(qty)

                # Perishability
                perish = round(random.uniform(*cat["perish_range"]), 1)

                # Urgency driven by perishability: shorter shelf-life -> higher urgency
                if perish <= 6:
                    urgency = weighted_choice({"LOW": 2, "MEDIUM": 20, "HIGH": 55, "CRITICAL": 23})
                elif perish <= 16:
                    urgency = weighted_choice({"LOW": 10, "MEDIUM": 45, "HIGH": 35, "CRITICAL": 10})
                else:
                    urgency = weighted_choice({"LOW": 30, "MEDIUM": 50, "HIGH": 18, "CRITICAL": 2})

                record = {
                    "date": current.isoformat(),
                    "organization": supplier["name"],
                    "organization_id": supplier["org_id"],
                    "org_type": supplier["org_type"],
                    "category": cat_name,
                    "quantity": qty,
                    "unit": cat["unit"],
                    "storage_condition": cat["storage"],
                    "perishability_hours": perish,
                    "urgency": urgency,
                    "is_event_day": is_event_day(current),
                    "day_of_week": current.strftime("%A"),
                    "month": current.month,
                    "is_weekend": current.weekday() >= 5,
                    "is_simulated": True,
                }
                records.append(record)

        current += timedelta(days=1)

    return records


# ─── Generate Demand Records ──────────────────────────────────────────────────
def generate_demand_records():
    records = []
    current = START_DATE
    while current <= END_DATE:
        for receiver in RECEIVERS:
            # Demand generated most days for shelters/food banks
            demand_prob = 0.85 if receiver["org_type"] in ("COMMUNITY_SHELTER", "FOOD_BANK") else 0.65
            # Slightly reduced on Sundays for NGOs
            if current.weekday() == 6 and receiver["org_type"] == "NGO":
                demand_prob *= 0.5

            if random.random() > demand_prob:
                continue

            cat_name = random.choice(receiver["preferred_categories"])
            cat = CAT_MAP[cat_name]

            # Base quantity: receivers typically request 60-90% of surplus baseline
            base_req = random.uniform(cat["qty_range"][0] * 0.6, cat["qty_range"][1] * 0.9)
            req_qty = (
                base_req
                * receiver["need_scale"]
                * seasonal_factor(current, cat_name)
                * end_of_month_factor(current)
            )
            # Weekend bump: shelters serve more people on weekends
            if current.weekday() >= 5 and receiver["org_type"] in ("COMMUNITY_SHELTER", "FOOD_BANK"):
                req_qty *= random.uniform(1.1, 1.35)

            req_qty = noisy(req_qty)

            urgency = weighted_choice(receiver["typical_urgency_weights"])

            record = {
                "date": current.isoformat(),
                "organization": receiver["name"],
                "organization_id": receiver["org_id"],
                "org_type": receiver["org_type"],
                "category": cat_name,
                "requested_quantity": req_qty,
                "unit": cat["unit"],
                "urgency": urgency,
                "is_event_day": is_event_day(current),
                "day_of_week": current.strftime("%A"),
                "month": current.month,
                "is_weekend": current.weekday() >= 5,
                "is_simulated": True,
            }
            records.append(record)

        current += timedelta(days=1)

    return records


# ─── Write CSV ────────────────────────────────────────────────────────────────
def write_csv(filepath, records):
    if not records:
        print("  [WARN] No records to write to {}".format(filepath))
        return
    fieldnames = list(records[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("ReSource Phase 3.1 -- Historical Data Generator")
    print("DISCLAIMER: All data is SYNTHETIC/SIMULATED (is_simulated=True)")
    print("=" * 70)

    data_dir = os.path.dirname(os.path.abspath(__file__))
    surplus_path = os.path.join(data_dir, "historical_surplus.csv")
    demand_path  = os.path.join(data_dir, "historical_demand.csv")

    print("\n[1/4] Generating historical surplus records ...")
    surplus_records = generate_surplus_records()
    print("      Generated {:,} surplus records".format(len(surplus_records)))

    print("[2/4] Generating historical demand records ...")
    demand_records = generate_demand_records()
    print("      Generated {:,} demand records".format(len(demand_records)))

    print("[3/4] Writing {} ...".format(surplus_path))
    write_csv(surplus_path, surplus_records)
    print("      Wrote {:,} rows -> historical_surplus.csv".format(len(surplus_records)))

    print("[4/4] Writing {} ...".format(demand_path))
    write_csv(demand_path, demand_records)
    print("      Wrote {:,} rows -> historical_demand.csv".format(len(demand_records)))

    # Summary
    print("\n" + "-" * 70)
    print("SUMMARY")
    print("-" * 70)

    s_dates = sorted({r["date"] for r in surplus_records})
    d_dates = sorted({r["date"] for r in demand_records})
    s_cats  = sorted({r["category"] for r in surplus_records})
    d_cats  = sorted({r["category"] for r in demand_records})
    s_orgs  = sorted({r["organization"] for r in surplus_records})
    d_orgs  = sorted({r["organization"] for r in demand_records})

    print("  Surplus records   : {:,}".format(len(surplus_records)))
    print("  Demand  records   : {:,}".format(len(demand_records)))
    print("  Date range        : {}  to  {}".format(s_dates[0], s_dates[-1]))
    print("  Surplus categories: {}".format(", ".join(s_cats)))
    print("  Demand  categories: {}".format(", ".join(d_cats)))
    print("  Supplier orgs     : {}".format(", ".join(s_orgs)))
    print("  Receiver orgs     : {}".format(", ".join(d_orgs)))
    print("  is_simulated      : True on every row (enforced at generation)")
    print("-" * 70)
    print("Done.  Next step: run data/validate_historical_data.py")


if __name__ == "__main__":
    main()
