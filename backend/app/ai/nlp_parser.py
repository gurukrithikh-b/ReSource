"""
ReSource AI/NLP Module - Deterministic Intake Parser (Asia/Kolkata Timezone Aware)

Extracts structured resource attributes from unstructured natural language text
for commercial food surplus and NGO demand intake workflows.
Designed with a modular class interface for future LLM wrapper extension.
"""

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional

# Business timezone requirement: Asia/Kolkata (IST)
APP_TIMEZONE = ZoneInfo("Asia/Kolkata")

class BaseResourceParser:
    """Abstract/Base interface for resource intake parsers (Deterministic & LLM wrappers)."""
    def parse_listing_text(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError

class DeterministicNLPParser(BaseResourceParser):
    def __init__(self):
        # Known storage conditions map
        self.storage_keywords = {
            "REFRIGERATED": ["refrigerat", "fridge", "chilled", "cold storage", "cool"],
            "FROZEN": ["frozen", "freezer", "ice"],
            "AMBIENT": ["ambient", "room temp", "pantry", "dry storage", "shelved"]
        }

        # Known units
        self.unit_patterns = [
            (r"\b(kg|kilograms?|kilos?)\b", "kg"),
            (r"\b(meals?|portions?|packed meals?|servings?|plates?)\b", "meals"),
            (r"\b(boxes?|crates?|cartons?)\b", "boxes"),
            (r"\b(loaves?|loaves of bread|breads?)\b", "loaves"),
            (r"\b(items?|parcels?|packages?|bags?)\b", "items")
        ]

        # Food subtypes
        self.subtype_keywords = [
            ("vegetarian", ["vegetarian", "veg ", "veg,", "veg.", "plant-based"]),
            ("vegan", ["vegan"]),
            ("non-vegetarian", ["non-veg", "chicken", "meat", "beef", "fish", "pork", "poultry"]),
            ("bakery", ["bakery", "bread", "pastry", "pastries", "sourdough", "croissant", "cake"]),
            ("fresh produce", ["produce", "fruit", "fruits", "vegetable", "vegetables", "veggies", "apples", "bananas"]),
            ("cooked meals", ["curry", "rice", "banquet", "buffet", "dinner", "lunch", "stew", "soup", "pasta"])
        ]

        # Urgency levels (for demand)
        self.urgency_keywords = {
            "CRITICAL": ["emergency", "critical", "immediate", "urgent!", "asap", "disaster"],
            "HIGH": ["high priority", "high urgency", "urgent", "tonight", "this evening", "today"],
            "MEDIUM": ["medium", "standard", "weekly", "tomorrow"],
            "LOW": ["low priority", "flexible", "next week", "anytime"]
        }

    def parse_listing_text(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "raw_text": "",
                "resource_type": None,
                "quantity": None,
                "unit": None,
                "storage_condition": None,
                "perishability_hours": None,
                "expires_at": None,
                "required_by": None,
                "deadline_display": None,
                "food_subtype": None,
                "urgency_level": None,
                "confidence": 0.0,
                "extracted_fields": {}
            }

        clean_text = text.strip()
        text_lower = clean_text.lower()
        extracted_fields = {}

        # 1. Quantity & Unit Extraction
        quantity = None
        unit = None

        qty_match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?", text_lower)
        if qty_match:
            try:
                val = float(qty_match.group(1))
                if val > 0:
                    quantity = val
                    extracted_fields["quantity"] = quantity
            except ValueError:
                pass

        for pattern, u_symbol in self.unit_patterns:
            if re.search(pattern, text_lower):
                unit = u_symbol
                extracted_fields["unit"] = unit
                break

        if not unit and quantity is not None:
            unit = "kg"
            extracted_fields["unit"] = unit

        # 2. Storage Condition
        storage_condition = None
        for cond, kws in self.storage_keywords.items():
            if any(kw in text_lower for kw in kws):
                storage_condition = cond
                extracted_fields["storage_condition"] = storage_condition
                break

        # 3. Food Subtype & Resource Type
        food_subtype = None
        for st_name, kws in self.subtype_keywords:
            if any(kw in text_lower for kw in kws):
                food_subtype = st_name
                extracted_fields["food_subtype"] = food_subtype
                break

        resource_type = "Food Surplus"
        if food_subtype in ["cooked meals", "vegetarian", "vegan", "non-vegetarian"]:
            resource_type = "Cooked Meals"
        elif food_subtype == "bakery":
            resource_type = "Bakery Items"
        elif food_subtype == "fresh produce":
            resource_type = "Fresh Produce"

        extracted_fields["resource_type"] = resource_type

        # 4. Timezone-Aware Perishability & Deadline Handling (Asia/Kolkata)
        perishability_hours = None
        expires_at = None
        required_by = None
        deadline_display = None
        now_tz = datetime.now(APP_TIMEZONE)

        # Match relative hours, e.g. "within 8 hours", "for 24 hrs", "8 hours", "6h"
        hours_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b", text_lower)
        if hours_match:
            try:
                perishability_hours = float(hours_match.group(1))
                extracted_fields["perishability_hours"] = perishability_hours
            except ValueError:
                pass

        # Match explicit time of day, e.g. "until 9 PM", "until 9:00 PM today", "by 8:30 PM", "before 7 PM"
        time_match = re.search(r"(?:until|by|before)\s*(\d{1,2})(?::(\d{2}))?\s*(pm|am)\b", text_lower)
        if time_match:
            hour_digit = int(time_match.group(1))
            minute_digit = int(time_match.group(2)) if time_match.group(2) else 0
            ampm = time_match.group(3)
            if ampm == "pm" and hour_digit < 12:
                hour_digit += 12
            elif ampm == "am" and hour_digit == 12:
                hour_digit = 0

            # Target datetime in Asia/Kolkata (IST)
            target_time = now_tz.replace(hour=hour_digit, minute=minute_digit, second=0, microsecond=0)
            if target_time <= now_tz:
                target_time += timedelta(days=1)

            # Perishability hours is the remaining duration from current IST time to target time
            diff_hours = max(0.5, round((target_time - now_tz).total_seconds() / 3600.0, 1))
            if perishability_hours is None:
                perishability_hours = diff_hours

            expires_at = target_time
            required_by = target_time

            # Format human-friendly deadline display (e.g. "9:00 PM today")
            time_formatted = target_time.strftime("%I:%M %p").lstrip("0")
            if target_time.date() == now_tz.date():
                deadline_display = f"{time_formatted} today"
            elif target_time.date() == (now_tz.date() + timedelta(days=1)):
                deadline_display = f"{time_formatted} tomorrow"
            else:
                deadline_display = target_time.strftime("%b %d, %I:%M %p")

            extracted_fields["deadline_display"] = deadline_display

        # Fallback if perishability_hours given without explicit time of day
        if perishability_hours and not expires_at:
            expires_at = now_tz + timedelta(hours=perishability_hours)
            required_by = expires_at
            time_formatted = expires_at.strftime("%I:%M %p").lstrip("0")
            if expires_at.date() == now_tz.date():
                deadline_display = f"{time_formatted} today"
            elif expires_at.date() == (now_tz.date() + timedelta(days=1)):
                deadline_display = f"{time_formatted} tomorrow"
            else:
                hrs_str = int(perishability_hours) if perishability_hours.is_integer() else perishability_hours
                deadline_display = f"{time_formatted} (in {hrs_str} hrs)"

        # Default fallback if perishability absent
        if perishability_hours is None:
            perishability_hours = 12.0
            expires_at = now_tz + timedelta(hours=12)
            required_by = expires_at
            time_formatted = expires_at.strftime("%I:%M %p").lstrip("0")
            deadline_display = f"{time_formatted} (in 12 hrs)"

        # 5. Urgency Level (Demand focus)
        urgency_level = "MEDIUM"
        for surg, kws in self.urgency_keywords.items():
            if any(kw in text_lower for kw in kws):
                urgency_level = surg
                extracted_fields["urgency_level"] = urgency_level
                break

        # 6. Confidence Score Calculation
        score = 0.0
        if quantity is not None:
            score += 0.35
        if unit is not None:
            score += 0.15
        if storage_condition is not None:
            score += 0.20
        if perishability_hours is not None or expires_at is not None:
            score += 0.15
        if food_subtype is not None:
            score += 0.15

        confidence = round(min(1.0, max(0.2, score)), 2)

        return {
            "raw_text": clean_text,
            "resource_type": resource_type,
            "quantity": quantity,
            "unit": unit or "kg",
            "storage_condition": storage_condition,
            "perishability_hours": perishability_hours,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "required_by": required_by.isoformat() if required_by else None,
            "deadline_display": deadline_display,
            "food_subtype": food_subtype,
            "urgency_level": urgency_level,
            "confidence": confidence,
            "extracted_fields": extracted_fields
        }

# Global instance export
nlp_parser = DeterministicNLPParser()
