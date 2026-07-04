# ============================================================
# RISK RULE ENGINE
# Ratio thresholds and red flags
# ============================================================

RISK_THRESHOLDS = {
    "cashflow_min": 0,
    "tax_liability_max": 300000,
    "ratio_min": 1.0,
    "gst_mismatch_max": 10000,
    "tds_mismatch_max": 5000
}

# ============================================================
# CASHFLOW RISK
# ============================================================

def evaluate_cashflow_risk(value):
    if value < RISK_THRESHOLDS["cashflow_min"]:
        return "Negative Cash Flow Risk"
    return None

# ============================================================
# TAX RISK
# ============================================================

def evaluate_tax_risk(value):
    if value > RISK_THRESHOLDS["tax_liability_max"]:
        return "High Tax Liability Risk"
    return None

# ============================================================
# FINANCIAL RATIO RISK
# ============================================================

def evaluate_ratio_risk(value):
    if value < RISK_THRESHOLDS["ratio_min"]:
        return "Weak Financial Ratio Risk"
    return None

# ============================================================
# GST RISK
# ============================================================

def evaluate_gst_risk(value):
    if value > RISK_THRESHOLDS["gst_mismatch_max"]:
        return "GST Compliance Risk"
    return None

# ============================================================
# TDS RISK
# ============================================================

def evaluate_tds_risk(value):
    if value > RISK_THRESHOLDS["tds_mismatch_max"]:
        return "TDS Compliance Risk"
    return None
