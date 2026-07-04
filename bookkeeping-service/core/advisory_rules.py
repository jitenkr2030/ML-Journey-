import pandas as pd

# ============================================================
# CLIENT ADVISORY RULES
# ============================================================

ADVISORY_RULES = {
    "low_profit_margin": "Review pricing strategy and reduce unnecessary expenses.",
    "high_gst_payable": "Ensure GST input credits are properly claimed.",
    "high_tds_payable": "Deposit TDS before due dates to avoid penalties.",
    "negative_cash_flow": "Improve receivable collection and control spending.",
    "high_bank_charges": "Negotiate banking fees or optimize transactions.",
    "high_salary_ratio": "Evaluate payroll efficiency and staffing productivity.",
    "high_rent_ratio": "Assess office cost optimization opportunities."
}

# ============================================================
# GENERATE ADVISORY
# ============================================================

def generate_advisory(risk_flags):
    recommendations = []

    for flag in risk_flags:
        if flag in ADVISORY_RULES:
            recommendations.append(
                ADVISORY_RULES[flag]
            )

    return recommendations

# ============================================================
# SAVE ADVISORY
# ============================================================

def save_advisory(output_path, recommendations):
    df = pd.DataFrame({
        "Recommendation": recommendations
    })

    df.to_csv(
        output_path,
        index=False
    )

    return output_path
