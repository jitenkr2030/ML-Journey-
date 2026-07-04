# ============================================================
# TAX RULE ENGINE
# ============================================================

from typing import Dict

# ============================================================
# TAX SLABS
# ============================================================

TAX_SLABS = [
    (250000, 0),
    (500000, 5),
    (1000000, 20),
    (999999999, 30)
]

# ============================================================
# STANDARD DEDUCTIONS
# ============================================================

STANDARD_DEDUCTIONS: Dict[str, float] = {
    "salary": 50000,
    "business": 0
}

# ============================================================
# SECTION LIMITS
# ============================================================

SECTION_LIMITS: Dict[str, float] = {
    "80C": 150000,
    "80D": 25000,
    "80TTA": 10000,
    "80G": 50000
}

# ============================================================
# STANDARD DEDUCTION
# ============================================================

def apply_standard_deduction(
    income: float,
    income_type: str = "salary"
):
    deduction = STANDARD_DEDUCTIONS.get(
        income_type.lower(),
        0
    )

    taxable_income = max(
        income - deduction,
        0
    )

    return round(taxable_income, 2)

# ============================================================
# SECTION DEDUCTIONS
# ============================================================

def apply_section_deductions(
    taxable_income: float,
    deductions: Dict[str, float]
):
    total_deduction = 0

    for section, amount in deductions.items():
        allowed_limit = SECTION_LIMITS.get(
            section.upper(),
            0
        )

        total_deduction += min(
            amount,
            allowed_limit
        )

    final_income = max(
        taxable_income - total_deduction,
        0
    )

    return round(final_income, 2), round(total_deduction, 2)

# ============================================================
# TAX CALCULATION
# ============================================================

def calculate_tax(income: float):
    tax = 0
    previous_limit = 0

    for slab_limit, rate in TAX_SLABS:
        if income > slab_limit:
            taxable_part = slab_limit - previous_limit
        else:
            taxable_part = income - previous_limit

        if taxable_part > 0:
            tax += taxable_part * (rate / 100)

        previous_limit = slab_limit

        if income <= slab_limit:
            break

    return round(tax, 2)

# ============================================================
# ADVANCE TAX CALCULATION
# ============================================================

def calculate_advance_tax(total_tax: float):
    advance_tax = {
        "Q1_15%": round(total_tax * 0.15, 2),
        "Q2_45%": round(total_tax * 0.45, 2),
        "Q3_75%": round(total_tax * 0.75, 2),
        "Q4_100%": round(total_tax * 1.00, 2)
    }

    return advance_tax

# ============================================================
# TOTAL ADVANCE TAX
# ============================================================

def get_total_advance_tax(total_tax: float):
    adv = calculate_advance_tax(total_tax)
    return round(sum(adv.values()), 2)

