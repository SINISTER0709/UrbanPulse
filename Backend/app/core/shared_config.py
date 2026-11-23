"""
UrbanPulse Platform - Day-0 Freeze Shared Configuration.
Defines locked category keys, department mappings, and priority formula weights.
"""
from typing import Dict, List, Any
from app.models.enums import Day0Category

# 1. Day-0 Locked Categories (Strictly 6 categories)
LOCKED_DAY0_CATEGORIES: List[str] = [
    Day0Category.road_damage.value,
    Day0Category.garbage_sanitation.value,
    Day0Category.streetlight_electrical.value,
    Day0Category.water_supply.value,
    Day0Category.drainage_flooding.value,
    Day0Category.other.value,
]

LOCKED_CATEGORIES = LOCKED_DAY0_CATEGORIES

# 2. Configurable Department Mappings (Day-0 Freeze)
CATEGORY_DEPARTMENT_MAPPINGS: Dict[str, str] = {
    Day0Category.road_damage.value: "Public Works",
    Day0Category.garbage_sanitation.value: "Solid Waste Management",
    Day0Category.streetlight_electrical.value: "Electrical & Energy",
    Day0Category.water_supply.value: "Water Supply & Sewerage",
    Day0Category.drainage_flooding.value: "Stormwater Drainage",
    Day0Category.other.value: "General Administration",
}

# 3. 5-Factor Priority Formula Weights (Page 4: P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E)
PRIORITY_WEIGHTS: Dict[str, float] = {
    "S": 0.40,  # Severity (from ML / LLM prediction)
    "R": 0.20,  # Repeat reports / Frequency
    "T": 0.15,  # Time decay / Age of issue
    "L": 0.15,  # Location risk (proximity to sensitive POIs)
    "E": 0.10,  # Escalation history
}

# 4. Sensitive POI Types for Location Risk (L) calculations
SENSITIVE_POI_TYPES: List[str] = [
    "school",
    "hospital",
    "transit_hub",
    "metro_station",
    "fire_station",
    "major_junction",
]

def get_day0_config() -> Dict[str, Any]:
    """Returns the immutable Day-0 configuration bundle."""
    return {
        "locked_categories": LOCKED_DAY0_CATEGORIES,
        "department_mappings": CATEGORY_DEPARTMENT_MAPPINGS,
        "priority_weights": PRIORITY_WEIGHTS,
        "priority_formula": "P = 0.40*S + 0.20*R + 0.15*T + 0.15*L + 0.10*E",
        "sensitive_poi_types": SENSITIVE_POI_TYPES,
        "version": "Day-0 Freeze v1.0",
    }
