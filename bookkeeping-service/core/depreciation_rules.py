# ============================================================
# DEPRECIATION RULE ENGINE
# ============================================================

from typing import Dict

# ============================================================
# DEPRECIATION RATES
# ============================================================

DEPRECIATION_RATES: Dict[str, float] = {
    "computer": 40.0,
    "laptop": 40.0,
    "software": 40.0,
    "furniture": 10.0,
    "office_equipment": 15.0,
    "vehicle": 15.0,
    "plant_machinery": 15.0,
    "building": 10.0,
    "mobile": 15.0,
    "generator": 15.0,
    "air_conditioner": 15.0
}

# ============================================================
# CLASSIFY ASSET TYPE
# ============================================================

def classify_asset_type(asset_name: str) -> str:
    asset_name = asset_name.lower().strip()

    if "computer" in asset_name:
        return "computer"
    elif "laptop" in asset_name:
        return "laptop"
    elif "software" in asset_name:
        return "software"
    elif "chair" in asset_name or "table" in asset_name:
        return "furniture"
    elif "printer" in asset_name:
        return "office_equipment"
    elif "car" in asset_name or "bike" in asset_name:
        return "vehicle"
    elif "machine" in asset_name:
        return "plant_machinery"
    elif "building" in asset_name:
        return "building"
    elif "mobile" in asset_name:
        return "mobile"
    elif "generator" in asset_name:
        return "generator"
    elif "ac" in asset_name:
        return "air_conditioner"

    return "office_equipment"

# ============================================================
# GET RATE
# ============================================================

def get_depreciation_rate(asset_name: str) -> float:
    asset_type = classify_asset_type(asset_name)
    return DEPRECIATION_RATES.get(asset_type, 10.0)

# ============================================================
# WDV METHOD
# ============================================================

def calculate_wdv(amount: float, rate: float):
    depreciation = amount * (rate / 100)
    closing_value = amount - depreciation
    return round(depreciation, 2), round(closing_value, 2)

# ============================================================
# SLM METHOD
# ============================================================

def calculate_slm(amount: float, useful_life: int):
    if useful_life <= 0:
        useful_life = 1

    depreciation = amount / useful_life
    closing_value = amount - depreciation

    return round(depreciation, 2), round(closing_value, 2)

# ============================================================
# DEFAULT CALCULATOR
# ============================================================

def calculate_depreciation(asset_name: str, amount: float):
    rate = get_depreciation_rate(asset_name)
    depreciation, closing_value = calculate_wdv(amount, rate)

    return {
        "asset_type": classify_asset_type(asset_name),
        "rate": rate,
        "depreciation": depreciation,
        "closing_value": closing_value
    }

