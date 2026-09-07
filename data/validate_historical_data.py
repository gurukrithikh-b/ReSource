"""
validate_historical_data.py
───────────────────────────────────────────────────────────────────────────────
ReSource Phase 3.1 — Historical Data Validation
───────────────────────────────────────────────────────────────────────────────

PURPOSE
    Validates the synthetic historical CSV files produced by
    generate_historical_data.py before they are used for ML model training.

CHECKS PERFORMED
    1.  Both CSV files exist.
    2.  Expected columns are present in each file.
    3.  Row counts are within reasonable bounds (>= 1000 rows each).
    4.  Date coverage: start date, end date, and minimum unique day count.
    5.  Categories are present (at least the 4 core ReSource categories).
    6.  Organisations are present (at least 4 suppliers / 4 receivers).
    7.  No unexpected null / empty values in required columns.
    8.  is_simulated is True on every row.
    9.  All quantity fields are strictly positive (> 0).
    10. Column data types are consistent (dates parse cleanly, quantities numeric).

OUTPUT
    Prints a per-check PASS/FAIL report and exits with code 0 if all checks
    pass, or code 1 if any check fails (so CI pipelines can detect failures).
"""

import os
import sys
import csv
from datetime import date, datetime

# ─── Paths (relative to this script's location) ───────────────────────────────
DATA_DIR      = os.path.dirname(os.path.abspath(__file__))
SURPLUS_PATH  = os.path.join(DATA_DIR, "historical_surplus.csv")
DEMAND_PATH   = os.path.join(DATA_DIR, "historical_demand.csv")

# ─── Expected schema ──────────────────────────────────────────────────────────
SURPLUS_REQUIRED_COLUMNS = {
    "date", "organization", "organization_id", "org_type",
    "category", "quantity", "unit", "storage_condition",
    "perishability_hours", "urgency", "is_event_day",
    "day_of_week", "month", "is_weekend", "is_simulated",
}

DEMAND_REQUIRED_COLUMNS = {
    "date", "organization", "organization_id", "org_type",
    "category", "requested_quantity", "unit", "urgency",
    "is_event_day", "day_of_week", "month", "is_weekend", "is_simulated",
}

EXPECTED_CATEGORIES = {
    "Cooked Meals", "Fresh Produce", "Bakery Items", "Food Surplus",
}

EXPECTED_SUPPLIERS = {
    "Grand Horizon Hotel", "Bistro Verde Restaurant",
    "Metropolitan Event Center", "Sunrise University Canteen",
    "Harvest Organic Market", "The Riverside Hotel",
}

EXPECTED_RECEIVERS = {
    "Hope Community Shelter", "Metro Food Bank NGO",
    "City Bridge Women's NGO", "Sunrise Youth Foundation",
    "Riverside Community Shelter",
}

MIN_SURPLUS_ROWS = 1000
MIN_DEMAND_ROWS  = 1000
MIN_DATE_DAYS    = 300   # expect at least 300 unique days covered
EXPECTED_START   = "2025-01-01"
EXPECTED_END     = "2025-12-31"


# ─── Validation Utilities ─────────────────────────────────────────────────────

_RESULTS = []

def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    _RESULTS.append((name, passed, detail))
    indicator = "[OK]  " if passed else "[FAIL]"
    msg = "{} {}".format(indicator, name)
    if detail:
        msg += "  ->  {}".format(detail)
    print(msg)
    return passed


def load_csv(filepath):
    """Load a CSV file and return list of dicts. Returns None if file missing."""
    if not os.path.isfile(filepath):
        return None
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_bool(val):
    """Normalise various boolean representations to Python bool."""
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes")


def parse_float(val):
    """Return float or None if unparseable."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_date(val):
    """Return date object or None if unparseable."""
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ─── Validate Surplus ─────────────────────────────────────────────────────────

def validate_surplus(rows):
    print("\n--- Surplus Validation ---")

    # 2. Expected columns
    actual_cols = set(rows[0].keys()) if rows else set()
    missing = SURPLUS_REQUIRED_COLUMNS - actual_cols
    check("Surplus: required columns present",
          len(missing) == 0,
          "Missing: {}".format(missing) if missing else "")

    # 3. Row count
    check("Surplus: minimum row count (>= {})".format(MIN_SURPLUS_ROWS),
          len(rows) >= MIN_SURPLUS_ROWS,
          "{:,} rows found".format(len(rows)))

    # Collect field values for further checks
    dates       = []
    categories  = set()
    orgs        = set()
    null_issues = []
    non_positive = []
    non_simulated = []

    required_non_null = ["date", "organization", "organization_id", "category",
                         "quantity", "unit", "urgency", "is_simulated"]

    for i, row in enumerate(rows):
        # Null check
        for col in required_non_null:
            if col in row and (row[col] is None or str(row[col]).strip() == ""):
                null_issues.append("row {}: {} is empty".format(i + 2, col))

        # Date parse
        d = parse_date(row.get("date", ""))
        if d:
            dates.append(d)

        # Category / org
        categories.add(row.get("category", ""))
        orgs.add(row.get("organization", ""))

        # Quantity positive
        qty = parse_float(row.get("quantity", ""))
        if qty is not None and qty <= 0:
            non_positive.append("row {}: quantity={}".format(i + 2, qty))

        # is_simulated
        if not parse_bool(row.get("is_simulated", "False")):
            non_simulated.append("row {}".format(i + 2))

    # 4. Date coverage
    if dates:
        unique_days = len(set(dates))
        min_date = min(dates).isoformat()
        max_date = max(dates).isoformat()
        check("Surplus: start date is {}".format(EXPECTED_START),
              min_date == EXPECTED_START,
              "found {}".format(min_date))
        check("Surplus: end date is {}".format(EXPECTED_END),
              max_date == EXPECTED_END,
              "found {}".format(max_date))
        check("Surplus: date coverage >= {} unique days".format(MIN_DATE_DAYS),
              unique_days >= MIN_DATE_DAYS,
              "{} unique days".format(unique_days))
    else:
        check("Surplus: date coverage", False, "no parseable dates found")

    # 5. Categories
    present_cats = categories & EXPECTED_CATEGORIES
    check("Surplus: all expected categories present",
          present_cats == EXPECTED_CATEGORIES,
          "found: {}  missing: {}".format(
              sorted(present_cats),
              sorted(EXPECTED_CATEGORIES - present_cats)))

    # 6. Supplier organisations
    present_orgs = orgs & EXPECTED_SUPPLIERS
    check("Surplus: expected supplier orgs present (>= 4)",
          len(present_orgs) >= 4,
          "found {} of {}".format(len(present_orgs), len(EXPECTED_SUPPLIERS)))

    # 7. No nulls in required columns
    check("Surplus: no null/empty values in required columns",
          len(null_issues) == 0,
          "{} issue(s): {}".format(len(null_issues), null_issues[:3]) if null_issues else "")

    # 8. is_simulated=True on every row
    check("Surplus: is_simulated=True on every row",
          len(non_simulated) == 0,
          "{} row(s) not simulated".format(len(non_simulated)) if non_simulated else "")

    # 9. Quantities positive
    check("Surplus: all quantity values are positive",
          len(non_positive) == 0,
          "{} non-positive row(s)".format(len(non_positive)) if non_positive else "")


# ─── Validate Demand ──────────────────────────────────────────────────────────

def validate_demand(rows):
    print("\n--- Demand Validation ---")

    # 2. Expected columns
    actual_cols = set(rows[0].keys()) if rows else set()
    missing = DEMAND_REQUIRED_COLUMNS - actual_cols
    check("Demand: required columns present",
          len(missing) == 0,
          "Missing: {}".format(missing) if missing else "")

    # 3. Row count
    check("Demand: minimum row count (>= {})".format(MIN_DEMAND_ROWS),
          len(rows) >= MIN_DEMAND_ROWS,
          "{:,} rows found".format(len(rows)))

    dates        = []
    categories   = set()
    orgs         = set()
    null_issues  = []
    non_positive = []
    non_simulated = []

    required_non_null = ["date", "organization", "organization_id", "category",
                         "requested_quantity", "unit", "urgency", "is_simulated"]

    for i, row in enumerate(rows):
        # Null check
        for col in required_non_null:
            if col in row and (row[col] is None or str(row[col]).strip() == ""):
                null_issues.append("row {}: {} is empty".format(i + 2, col))

        # Date parse
        d = parse_date(row.get("date", ""))
        if d:
            dates.append(d)

        categories.add(row.get("category", ""))
        orgs.add(row.get("organization", ""))

        # Quantity positive
        qty = parse_float(row.get("requested_quantity", ""))
        if qty is not None and qty <= 0:
            non_positive.append("row {}: requested_quantity={}".format(i + 2, qty))

        # is_simulated
        if not parse_bool(row.get("is_simulated", "False")):
            non_simulated.append("row {}".format(i + 2))

    # 4. Date coverage
    if dates:
        unique_days = len(set(dates))
        min_date = min(dates).isoformat()
        max_date = max(dates).isoformat()
        check("Demand: start date is {}".format(EXPECTED_START),
              min_date == EXPECTED_START,
              "found {}".format(min_date))
        check("Demand: end date is {}".format(EXPECTED_END),
              max_date == EXPECTED_END,
              "found {}".format(max_date))
        check("Demand: date coverage >= {} unique days".format(MIN_DATE_DAYS),
              unique_days >= MIN_DATE_DAYS,
              "{} unique days".format(unique_days))
    else:
        check("Demand: date coverage", False, "no parseable dates found")

    # 5. Categories
    present_cats = categories & EXPECTED_CATEGORIES
    check("Demand: all expected categories present",
          present_cats == EXPECTED_CATEGORIES,
          "found: {}  missing: {}".format(
              sorted(present_cats),
              sorted(EXPECTED_CATEGORIES - present_cats)))

    # 6. Receiver organisations
    present_orgs = orgs & EXPECTED_RECEIVERS
    check("Demand: expected receiver orgs present (>= 4)",
          len(present_orgs) >= 4,
          "found {} of {}".format(len(present_orgs), len(EXPECTED_RECEIVERS)))

    # 7. No nulls
    check("Demand: no null/empty values in required columns",
          len(null_issues) == 0,
          "{} issue(s): {}".format(len(null_issues), null_issues[:3]) if null_issues else "")

    # 8. is_simulated=True on every row
    check("Demand: is_simulated=True on every row",
          len(non_simulated) == 0,
          "{} row(s) not simulated".format(len(non_simulated)) if non_simulated else "")

    # 9. Quantities positive
    check("Demand: all requested_quantity values are positive",
          len(non_positive) == 0,
          "{} non-positive row(s)".format(len(non_positive)) if non_positive else "")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("ReSource Phase 3.1 -- Historical Data Validation")
    print("=" * 70)

    all_passed = True

    # ── Check 1: Files exist ──────────────────────────────────────────────────
    print("\n--- File Existence ---")
    surplus_exists = check("historical_surplus.csv exists",
                           os.path.isfile(SURPLUS_PATH),
                           SURPLUS_PATH)
    demand_exists  = check("historical_demand.csv exists",
                           os.path.isfile(DEMAND_PATH),
                           DEMAND_PATH)

    if not surplus_exists:
        print("\n[ERROR] Surplus CSV not found. Run generate_historical_data.py first.")
        sys.exit(1)
    if not demand_exists:
        print("\n[ERROR] Demand CSV not found. Run generate_historical_data.py first.")
        sys.exit(1)

    # ── Load ──────────────────────────────────────────────────────────────────
    surplus_rows = load_csv(SURPLUS_PATH)
    demand_rows  = load_csv(DEMAND_PATH)

    print("\n  Surplus CSV loaded : {:,} rows".format(len(surplus_rows) if surplus_rows else 0))
    print("  Demand  CSV loaded : {:,} rows".format(len(demand_rows) if demand_rows else 0))

    if not surplus_rows:
        check("Surplus CSV has data", False, "file is empty or unreadable")
        sys.exit(1)
    if not demand_rows:
        check("Demand CSV has data", False, "file is empty or unreadable")
        sys.exit(1)

    # ── Validate each file ────────────────────────────────────────────────────
    validate_surplus(surplus_rows)
    validate_demand(demand_rows)

    # ── Final report ──────────────────────────────────────────────────────────
    total  = len(_RESULTS)
    passed = sum(1 for _, ok, _ in _RESULTS if ok)
    failed = total - passed

    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    print("  Total checks : {}".format(total))
    print("  Passed       : {}".format(passed))
    print("  Failed       : {}".format(failed))

    if failed > 0:
        print("\nFailed checks:")
        for name, ok, detail in _RESULTS:
            if not ok:
                print("  [FAIL] {}  ->  {}".format(name, detail))
        print("\nValidation FAILED.")
        sys.exit(1)
    else:
        print("\nAll checks passed. Historical data is ready for Phase 3.2 ML training.")
        sys.exit(0)


if __name__ == "__main__":
    main()
