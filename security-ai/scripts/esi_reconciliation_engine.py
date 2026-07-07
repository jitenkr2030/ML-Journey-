# security-ai/scripts/esi_reconciliation_engine.py
"""
Production-Grade ESI Reconciliation Engine
Security AI — Employee State Insurance Compliance System

═══════════════════════════════════════════════════════════════════
 23 MODULES | 80+ FUNCTIONS | 15+ REPORTS | AI RECOMMENDATIONS
═══════════════════════════════════════════════════════════════════

 MODULES:
  1.  Input Validation
  2.  Multi-Sheet Processing
  3.  Multi-Month Processing
  4.  Employee Matching (7-method cascade)
  5.  ESI Eligibility Validation
  6.  Contribution Validation
  7.  Compliance Rules Engine
  8.  Fraud Detection (8 detectors)
  9.  Attendance Cross-Validation
  10. Wage Register Validation
  11. Bank Validation
  12. Risk Scoring Engine
  13. AI Recommendation Engine
  14. Audit Trail
  15. Dashboard Summary
  16. Site-wise Summary
  17. Client-wise Summary
  18. Exception Report
  19. Excel Reports (multi-sheet)
  20. JSON API Output
  21. Performance Statistics
  22. Configuration System
  23. AI Features (anomaly detection)
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
import warnings
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# MODULE 22 — CONFIGURATION SYSTEM
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = BASE_DIR / "processed"
OUTPUT_DIR = BASE_DIR / "reconciliation"
EXPORT_DIR = BASE_DIR / "exports"
SUMMARY_DIR = BASE_DIR / "summaries"
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

for _d in (INPUT_DIR, OUTPUT_DIR, EXPORT_DIR, SUMMARY_DIR, LOG_DIR, CONFIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)


@dataclass
class ESIConfig:
    """All ESI parameters — loaded from config, never hardcoded."""
    esi_wage_limit: float = 21000.0
    employee_esi_rate: float = 0.0075      # 0.75%
    employer_esi_rate: float = 0.0325      # 3.25%
    tolerance_amount: float = 1.0          # ₹1 rounding tolerance
    tolerance_pct: float = 0.01            # 1% percentage error tolerance
    fuzzy_threshold: float = 0.70
    engine_version: str = "4.0.0"
    operator: str = "auto"
    months: List[str] = field(default_factory=lambda: [
        "april", "may", "june", "july", "august", "september",
        "october", "november", "december", "january", "february", "march",
    ])


@dataclass
class ClientConfig:
    """Per-client configuration."""
    client_name: str = "default"
    client_id: str = "001"
    sites: List[str] = field(default_factory=list)
    esi_config: ESIConfig = field(default_factory=ESIConfig)
    wages_file: str = "wages.csv"
    esi_file: str = "difference.csv"
    bank_file: str = "bank.csv"
    attendance_file: str = "attendance.csv"
    master_file: str = "employee_master.csv"


def load_config(config_path: Optional[Path] = None) -> ESIConfig:
    """Load ESI config from JSON or use defaults."""
    cfg = ESIConfig()
    if config_path and config_path.exists():
        try:
            with open(config_path) as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
            logger.info(f"Config loaded from {config_path}")
        except Exception as e:
            logger.warning(f"Config load error: {e}")
    return cfg


def load_rules(config: ESIConfig) -> Dict[str, Any]:
    """Build rule dictionary for validation engine."""
    return {
        "wage_limit": config.esi_wage_limit,
        "employee_rate": config.employee_esi_rate,
        "employer_rate": config.employer_esi_rate,
        "tolerance": config.tolerance_amount,
        "tolerance_pct": config.tolerance_pct,
    }


def load_client_config(client_name: str = "default") -> ClientConfig:
    """Load per-client settings."""
    path = CONFIG_DIR / f"esi_{client_name}.json"
    cfg = ClientConfig(client_name=client_name)
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
            for k, v in data.items():
                if k == "esi_config" and isinstance(v, dict):
                    cfg.esi_config = ESIConfig(**v)
                elif hasattr(cfg, k):
                    setattr(cfg, k, v)
        except Exception as e:
            logger.warning(f"Client config error: {e}")
    return cfg


# ============================================================
# MODULE 21 — PRODUCTION LOGGING
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(funcName)s:%(lineno)d | %(message)s"
)
LOG_DATE = "%Y-%m-%d %H:%M:%S"


def setup_rotating_logger(log_dir: Path) -> logging.Logger:
    """Production logging with rotation."""
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("ESIRecon")
    root.setLevel(logging.DEBUG)

    if root.handlers:
        return root

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(console)

    fh = RotatingFileHandler(
        log_dir / "esi_reconciliation.log",
        maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(fh)

    eh = RotatingFileHandler(
        log_dir / "esi_errors.log",
        maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    eh.setLevel(logging.ERROR)
    eh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(eh)

    return root


logger = setup_rotating_logger(LOG_DIR)

# ============================================================
# FIELD RESOLVER — Flexible Column Detection
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "employee_name": [
        "employee_name", "emp_name", "name", "staff_name",
        "worker_name", "Employee Name", "NAME",
    ],
    "employee_id": [
        "employee_id", "emp_id", "emp_code", "employee_code",
        "staff_id", "code",
    ],
    "uan_number": [
        "uan_number", "uan", "uan_no", "UAN",
    ],
    "ip_number": [
        "ip_number", "ip_no", "ip", "esic_ip", "esic_number",
        "esic_no", "ESIC No", "insurance_number",
    ],
    "bank_account": [
        "bank_account", "bank_account_number", "account_number",
        "bank_ac_no", "Account No",
    ],
    "pan_number": [
        "pan_number", "pan", "pan_no", "PAN",
    ],
    "aadhaar_number": [
        "aadhaar_number", "aadhaar", "aadhaar_no", "uid",
    ],
    "site_location": [
        "site_location", "site", "location", "branch", "unit",
        "Location",
    ],
    "basic_vda": [
        "basic_vda", "basic wages", "basic_wages", "basic",
        "basic + vda", "BASIC + VDA", "gross_wages", "gross",
    ],
    "gross_wages": [
        "gross_wages", "gross", "total_wages", "gross_salary",
        "gross pay",
    ],
    "employee_esi": [
        "employee_esi", "esic", "esi_deduction", "employee_esi_contribution",
        "ESIC 0.75%", "esic_employee", "ip_contribution",
    ],
    "employer_esi": [
        "employer_esi", "employer_esi_contribution", "employer_esic",
        "EMPLOYER SHARE OF ESIC", "er_contribution",
    ],
    "days_worked": [
        "days_worked", "working_days", "days_present", "days",
    ],
    "overtime_amount": [
        "overtime_amount", "ot_amount", "overtime", "ot",
    ],
    "net_pay": [
        "net_pay", "net_salary", "take_home",
    ],
    "joining_date": [
        "joining_date", "date_of_joining", "doj", "joining_dt",
    ],
    "exit_date": [
        "exit_date", "date_of_exit", "doe", "leaving_date",
        "resignation_date",
    ],
    "pay_month": [
        "pay_month", "month", "salary_month",
    ],
    "pay_year": [
        "pay_year", "year", "salary_year",
    ],
    "da": [
        "da", "dearness_allowance", "da_amount",
    ],
    "bonus": [
        "bonus", "bonus_amount", "exgratia",
    ],
    "leave_without_pay": [
        "lwp", "leave_without_pay", "lop", "unpaid_leave",
    ],
    "transfer_amount": [
        "transfer_amount", "bank_credit", "credited_amount",
    ],
    "transfer_date": [
        "transfer_date", "payment_date", "credit_date",
    ],
}


def find_column(df: pd.DataFrame, semantic: str) -> Optional[str]:
    aliases = COLUMN_ALIASES.get(semantic, [semantic])
    df_lower = {c.lower().strip(): c for c in df.columns}
    for a in aliases:
        if a.lower() in df_lower:
            return df_lower[a.lower()]
    for a in aliases:
        for dl, actual in df_lower.items():
            if a.lower() in dl and len(a) > 2:
                return actual
    return None


def build_column_map(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    return {sem: find_column(df, sem) for sem in COLUMN_ALIASES}


# ============================================================
# ENUMS
# ============================================================


class MatchType(str, Enum):
    EXACT_EMP_ID = "exact_employee_id"
    EXACT_UAN = "exact_uan"
    EXACT_IP = "exact_ip_number"
    EXACT_BANK = "exact_bank_account"
    EXACT_PAN = "exact_pan"
    EXACT_AADHAAR = "exact_aadhaar"
    FUZZY_NAME = "fuzzy_name"
    FUZZY_NAME_SITE = "fuzzy_name_site"
    NO_MATCH = "no_match"


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class ValidationResult:
    employee_name: str = ""
    employee_id: str = ""
    ip_number: str = ""
    site: str = ""
    validation_type: str = ""
    expected_value: float = 0.0
    actual_value: float = 0.0
    difference: float = 0.0
    percentage_error: float = 0.0
    status: str = ""
    severity: str = ""
    detail: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AuditEntry:
    timestamp: str = ""
    action: str = ""
    employee_name: str = ""
    employee_id: str = ""
    site: str = ""
    field_name: str = ""
    old_value: str = ""
    new_value: str = ""
    detail: str = ""
    engine_version: str = "4.0.0"
    operator: str = "auto"


@dataclass
class Recommendation:
    employee_name: str = ""
    employee_id: str = ""
    site: str = ""
    issue_type: str = ""
    reason: str = ""
    suggestion: str = ""
    priority: str = ""           # high / medium / low
    department: str = ""         # payroll / compliance / hr / finance
    estimated_impact: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RuntimeStats:
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_loaded: int = 0
    rows_loaded: int = 0
    matches_attempted: int = 0
    matches_found: int = 0
    exact_matches: int = 0
    fuzzy_matches: int = 0
    validations_run: int = 0
    validations_passed: int = 0
    validations_failed: int = 0
    duplicates_found: int = 0
    missing_found: int = 0
    fraud_flags: int = 0
    recommendations: int = 0
    errors: int = 0
    warnings: int = 0
    sites_processed: int = 0
    months_processed: int = 0

    def finish(self):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        e = self.end_time or time.perf_counter()
        return round(e - self.start_time, 3)

    @property
    def rows_per_sec(self) -> float:
        return round(self.rows_loaded / self.elapsed, 1) if self.elapsed > 0 else 0.0

    def summary(self) -> Dict[str, Any]:
        return {"elapsed_seconds": self.elapsed, "rows_per_second": self.rows_per_sec,
                **{k: v for k, v in self.__dict__.items()
                   if k not in ("start_time", "end_time")}}


# Global stores
_audit_log: List[AuditEntry] = []
_exception_log: List[Dict] = []
_recommendations: List[Recommendation] = []

# ============================================================
# MODULE 1 — INPUT VALIDATION
# ============================================================


def validate_required_columns(
    df: pd.DataFrame, required: List[str], source: str = ""
) -> List[str]:
    """Check that required columns exist."""
    missing = []
    for col_semantic in required:
        if not find_column(df, col_semantic):
            missing.append(col_semantic)
    if missing:
        err = f"[{source}] Missing required columns: {missing}"
        logger.error(err)
        log_exception("missing_columns", "", err, "critical")
    return missing


def validate_numeric_columns(
    df: pd.DataFrame, col_map: Dict[str, Optional[str]],
    numeric_fields: List[str],
) -> pd.DataFrame:
    """Flag non-numeric values in numeric columns."""
    issues = []
    for sem in numeric_fields:
        col = col_map.get(sem)
        if not col or col not in df.columns:
            continue
        non_numeric = pd.to_numeric(df[col], errors="coerce").isna() & df[col].notna()
        bad_rows = df[non_numeric]
        for idx, row in bad_rows.iterrows():
            issues.append({
                "row": idx, "column": col,
                "value": str(row.get(col, "")),
                "issue": "non_numeric_in_numeric_column",
            })
    if issues:
        logger.warning(f"Numeric validation: {len(issues)} issues found")
    return pd.DataFrame(issues) if issues else pd.DataFrame()


def validate_duplicate_rows(df: pd.DataFrame, source: str = "") -> pd.DataFrame:
    """Detect fully duplicate rows."""
    dups = df[df.duplicated(keep=False)]
    if not dups.empty:
        logger.warning(f"[{source}] {len(dups)} duplicate rows detected")
    return dups


def validate_missing_employee_ids(
    df: pd.DataFrame, col_map: Dict, source: str = ""
) -> int:
    """Count employees with no ID."""
    id_col = col_map.get("employee_id")
    name_col = col_map.get("employee_name")
    if not id_col:
        return 0
    if id_col not in df.columns:
        return 0
    missing = df[id_col].isna().sum()
    if missing > 0:
        logger.warning(f"[{source}] {missing} rows with missing employee ID")
    return int(missing)


def validate_negative_wages(
    df: pd.DataFrame, col_map: Dict, source: str = ""
) -> pd.DataFrame:
    """Flag negative wage values."""
    issues = []
    wage_sems = ["basic_vda", "gross_wages", "employee_esi", "employer_esi"]
    for sem in wage_sems:
        col = col_map.get(sem)
        if not col or col not in df.columns:
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        neg_mask = numeric < 0
        for idx in df[neg_mask].index:
            name_col = col_map.get("employee_name")
            issues.append({
                "employee_name": str(df.loc[idx].get(name_col, "")) if name_col else "",
                "column": col,
                "value": float(numeric.loc[idx]),
                "issue": "negative_wage",
            })
    return pd.DataFrame(issues) if issues else pd.DataFrame()


def run_input_validation(
    df: pd.DataFrame, col_map: Dict, source: str = ""
) -> Dict[str, Any]:
    """Execute all input validations."""
    results = {
        "missing_columns": validate_required_columns(
            df, ["employee_name", "basic_vda"], source
        ),
        "numeric_issues": validate_numeric_columns(
            df, col_map, ["basic_vda", "gross_wages", "employee_esi", "employer_esi"]
        ),
        "duplicate_rows": validate_duplicate_rows(df, source),
        "missing_ids": validate_missing_employee_ids(df, col_map, source),
        "negative_wages": validate_negative_wages(df, col_map, source),
    }
    total_issues = sum(
        len(v) if isinstance(v, (pd.DataFrame, list)) else v
        for v in results.values()
    )
    logger.info(f"[{source}] Input validation: {total_issues} total issues")
    return results


# ============================================================
# MODULE 2 — MULTI-SHEET PROCESSING
# ============================================================


def process_site_sheet(
    df: pd.DataFrame,
    site_name: str,
    config: ESIConfig,
) -> pd.DataFrame:
    """Process ESI reconciliation for one site sheet."""
    col_map = build_column_map(df)
    results = []
    name_col = col_map.get("employee_name", "")

    for _, row in df.iterrows():
        rd = row.to_dict()
        gross = pd.to_numeric(rd.get(col_map.get("gross_wages", "") or col_map.get("basic_vda", ""), 0), errors="coerce") or 0
        actual_emp = pd.to_numeric(rd.get(col_map.get("employee_esi", ""), 0), errors="coerce") or 0
        actual_er = pd.to_numeric(rd.get(col_map.get("employer_esi", ""), 0), errors="coerce") or 0

        eligible = gross <= config.esi_wage_limit
        expected_emp = round(gross * config.employee_esi_rate) if eligible else 0
        expected_er = round(gross * config.employer_esi_rate) if eligible else 0

        emp_diff = round(actual_emp - expected_emp, 2)
        er_diff = round(actual_er - expected_er, 2)

        status = "Matched" if abs(emp_diff) <= config.tolerance_amount and abs(er_diff) <= config.tolerance_amount else "Mismatch"

        results.append({
            "site": site_name,
            "employee_name": str(rd.get(name_col, "")),
            "gross_wages": gross,
            "esi_eligibility": "Applicable" if eligible else "Not Applicable",
            "expected_employee_esi": expected_emp,
            "actual_employee_esi": actual_emp,
            "employee_esi_diff": emp_diff,
            "expected_employer_esi": expected_er,
            "actual_employer_esi": actual_er,
            "employer_esi_diff": er_diff,
            "status": status,
        })

    return pd.DataFrame(results) if results else pd.DataFrame()


def process_all_sites(
    wages_df: pd.DataFrame,
    config: ESIConfig,
    site_column: Optional[str] = None,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Process ESI reconciliation site by site."""
    if not site_column or site_column not in wages_df.columns:
        result = process_site_sheet(wages_df, "ALL_SITES", config)
        return result, {"ALL_SITES": result}

    all_results = []
    site_frames = {}

    for site_val in wages_df[site_column].dropna().unique():
        site_name = str(site_val).strip()
        site_df = wages_df[wages_df[site_column].astype(str).str.strip() == site_name].copy()
        if site_df.empty:
            continue
        result = process_site_sheet(site_df, site_name, config)
        if not result.empty:
            all_results.append(result)
            site_frames[site_name] = result

    combined = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()
    return combined, site_frames


def merge_site_reports(site_frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merge all site reports into one."""
    frames = [df for df in site_frames.values() if not df.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ============================================================
# MODULE 3 — MULTI-MONTH PROCESSING
# ============================================================


def process_month(
    wages_df: pd.DataFrame,
    month: str,
    year: str,
    config: ESIConfig,
    month_col: Optional[str] = None,
    year_col: Optional[str] = None,
) -> pd.DataFrame:
    """Reconcile ESI for a specific month."""
    filtered = wages_df.copy()
    if month_col and month_col in wages_df.columns:
        filtered = filtered[
            filtered[month_col].astype(str).str.lower().str.strip()
            == month.lower().strip()
        ]
    if year_col and year_col in wages_df.columns:
        filtered = filtered[
            filtered[year_col].astype(str).str.strip() == str(year).strip()
        ]

    if filtered.empty:
        return pd.DataFrame()

    col_map = build_column_map(filtered)
    result = process_site_sheet(filtered, f"{month}_{year}", config)
    if not result.empty:
        result["month"] = month
        result["year"] = year
    return result


def compare_previous_month(
    current: pd.DataFrame,
    previous: pd.DataFrame,
) -> pd.DataFrame:
    """Compare ESI between two months."""
    if current.empty or previous.empty:
        return pd.DataFrame()

    name_col = "employee_name"
    if name_col not in current.columns or name_col not in previous.columns:
        return pd.DataFrame()

    prev_lookup = {}
    for _, row in previous.iterrows():
        key = normalize_name(row.get(name_col, ""))
        if key:
            prev_lookup[key] = row.to_dict()

    diffs = []
    for _, row in current.iterrows():
        rd = row.to_dict()
        name = str(rd.get(name_col, ""))
        norm = normalize_name(name)
        prev = prev_lookup.get(norm)

        curr_emp = rd.get("actual_employee_esi", 0) or 0
        curr_er = rd.get("actual_employer_esi", 0) or 0

        prev_emp = prev.get("actual_employee_esi", 0) if prev else 0
        prev_er = prev.get("actual_employer_esi", 0) if prev else 0

        diffs.append({
            "employee_name": name,
            "current_employee_esi": curr_emp,
            "previous_employee_esi": prev_emp,
            "employee_esi_change": round(curr_emp - prev_emp, 2),
            "current_employer_esi": curr_er,
            "previous_employer_esi": prev_er,
            "employer_esi_change": round(curr_er - prev_er, 2),
            "status": "new" if prev is None else (
                "increased" if curr_emp > prev_emp else (
                    "decreased" if curr_emp < prev_emp else "stable"
                )
            ),
        })

    return pd.DataFrame(diffs)


def calculate_monthly_variance(
    monthly_results: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Calculate variance trends across months."""
    summaries = []
    for key in sorted(monthly_results.keys()):
        df = monthly_results[key]
        if df.empty:
            continue
        total = len(df)
        matched = len(df[df.get("status", pd.Series()) == "Matched"]) if "status" in df.columns else 0
        total_diff = df["employee_esi_diff"].sum() if "employee_esi_diff" in df.columns else 0

        summaries.append({
            "month_year": key,
            "total_employees": total,
            "matched": matched,
            "mismatched": total - matched,
            "compliance_pct": round((matched / total * 100) if total else 0, 2),
            "total_esi_difference": round(float(total_diff), 2),
        })

    tdf = pd.DataFrame(summaries)
    if len(tdf) >= 2:
        tdf["trend"] = tdf["compliance_pct"].diff().apply(
            lambda x: "improving" if x and x > 0 else ("declining" if x and x < 0 else "stable")
        )
    elif not tdf.empty:
        tdf["trend"] = "baseline"
    return tdf


# ============================================================
# NAME NORMALIZATION
# ============================================================

TITLES = ["mr", "mrs", "ms", "miss", "dr", "prof", "shri", "smt", "kumari"]
RELATION = ["s/o", "so", "d/o", "do", "w/o", "wo", "c/o", "co",
            "son of", "daughter of", "wife of"]
STOP_WORDS = TITLES + RELATION


def normalize_name(name: Any) -> str:
    if pd.isna(name) or name is None:
        return ""
    s = str(name).lower().strip()
    s = re.sub(r"[^a-zA-Z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    words = [w for w in s.split() if w not in STOP_WORDS]
    return " ".join(words).upper()


# ============================================================
# MODULE 4 — EMPLOYEE MATCHING (7-METHOD CASCADE)
# ============================================================


def _build_index(df: pd.DataFrame, col: Optional[str]) -> Dict[str, int]:
    if col is None or col not in df.columns:
        return {}
    idx = {}
    for i, val in df[col].items():
        if pd.notna(val):
            key = str(val).strip().upper()
            if key and key not in ("NAN", "NONE"):
                if key not in idx:
                    idx[key] = i
    return idx


def _try_exact(val: Any, index: Dict[str, int], target_df: pd.DataFrame,
               match_type: str, confidence: float) -> Optional[Dict[str, Any]]:
    if pd.isna(val) or not str(val).strip():
        return None
    key = str(val).strip().upper()
    if key in index:
        row = target_df.iloc[index[key]].to_dict()
        return {"matched": True, "match_type": match_type,
                "confidence": confidence, "matched_record": row,
                "reason": f"Exact {match_type}: {key}"}
    return None


def match_employee_id(src, tgt, sm, tm):
    sc, tc = sm.get("employee_id"), tm.get("employee_id")
    if sc and tc:
        return _try_exact(src.get(sc), _build_index(tgt, tc), tgt, MatchType.EXACT_EMP_ID.value, 100.0)
    return None


def match_uan(src, tgt, sm, tm):
    sc, tc = sm.get("uan_number"), tm.get("uan_number")
    if sc and tc:
        return _try_exact(src.get(sc), _build_index(tgt, tc), tgt, MatchType.EXACT_UAN.value, 100.0)
    return None


def match_ip_number(src, tgt, sm, tm):
    sc, tc = sm.get("ip_number"), tm.get("ip_number")
    if sc and tc:
        return _try_exact(src.get(sc), _build_index(tgt, tc), tgt, MatchType.EXACT_IP.value, 100.0)
    return None


def match_bank(src, tgt, sm, tm):
    sc, tc = sm.get("bank_account"), tm.get("bank_account")
    if sc and tc:
        return _try_exact(src.get(sc), _build_index(tgt, tc), tgt, MatchType.EXACT_BANK.value, 97.0)
    return None


def match_pan(src, tgt, sm, tm):
    sc, tc = sm.get("pan_number"), tm.get("pan_number")
    if sc and tc:
        return _try_exact(src.get(sc), _build_index(tgt, tc), tgt, MatchType.EXACT_PAN.value, 98.0)
    return None


def match_aadhaar(src, tgt, sm, tm):
    sc, tc = sm.get("aadhaar_number"), tm.get("aadhaar_number")
    if sc and tc:
        return _try_exact(src.get(sc), _build_index(tgt, tc), tgt, MatchType.EXACT_AADHAAR.value, 98.0)
    return None


def fallback_fuzzy_match(
    source_name: str,
    source_site: str,
    target_df: pd.DataFrame,
    tgt_map: Dict,
    threshold: float = 0.70,
) -> Dict[str, Any]:
    """Fuzzy name matching with site-scoping."""
    tgt_name_col = tgt_map.get("employee_name")
    if not tgt_name_col or tgt_name_col not in target_df.columns:
        return {"matched": False, "match_type": "no_match", "confidence": 0.0, "reason": "No name column"}

    norm_src = normalize_name(source_name)
    if not norm_src:
        return {"matched": False, "match_type": "no_match", "confidence": 0.0, "reason": "Empty name"}

    target_names = target_df[tgt_name_col].dropna().tolist()
    norm_map = {normalize_name(n): str(n) for n in target_names if normalize_name(n)}
    norm_targets = list(norm_map.keys())

    if not norm_targets:
        return {"matched": False, "match_type": "no_match", "confidence": 0.0, "reason": "No targets"}

    # Site-scoped first
    tgt_site_col = tgt_map.get("site_location")
    if source_site and tgt_site_col and tgt_site_col in target_df.columns:
        site_mask = target_df[tgt_site_col].astype(str).str.upper().str.strip() == source_site.upper().strip()
        site_df = target_df[site_mask]
        if not site_df.empty:
            site_names = {normalize_name(n): str(n) for n in site_df[tgt_name_col].dropna() if normalize_name(n)}
            if site_names:
                result = process.extractOne(norm_src, list(site_names.keys()), scorer=fuzz.token_sort_ratio)
                if result:
                    matched, score, _ = result
                    sf = float(score) / 100.0
                    if sf >= threshold:
                        return {"matched": True, "match_type": MatchType.FUZZY_NAME_SITE.value,
                                "confidence": round(sf * 100, 1),
                                "reason": f"Fuzzy name+site ({sf:.0%})"}

    # Global
    result = process.extractOne(norm_src, norm_targets, scorer=fuzz.token_sort_ratio)
    if not result:
        return {"matched": False, "match_type": "no_match", "confidence": 0.0, "reason": "No match"}

    matched, score, _ = result
    sf = float(score) / 100.0
    if sf < threshold:
        return {"matched": False, "match_type": "rejected", "confidence": round(sf * 100, 1),
                "reason": f"Below threshold ({sf:.0%})"}

    return {"matched": True, "match_type": MatchType.FUZZY_NAME.value,
            "confidence": round(sf * 100, 1), "reason": f"Fuzzy name ({sf:.0%})"}


def cascade_match_employees(
    wages_df: pd.DataFrame,
    target_df: pd.DataFrame,
    src_map: Dict,
    tgt_map: Dict,
    config: ESIConfig,
) -> pd.DataFrame:
    """7-method cascade matching."""
    results = []
    name_col = src_map.get("employee_name", "")
    site_col = src_map.get("site_location")
    id_col = src_map.get("employee_id")
    ip_col = src_map.get("ip_number")

    for _, row in wages_df.iterrows():
        src = row.to_dict()
        src_name = str(src.get(name_col, ""))
        src_site = str(src.get(site_col, "")) if site_col else ""
        src_id = str(src.get(id_col, "")) if id_col else ""

        m = None
        for fn in [match_employee_id, match_uan, match_ip_number, match_bank, match_pan, match_aadhaar]:
            m = fn(src, tgt_df := target_df, src_map, tgt_map)
            if m and m.get("matched"):
                break

        if not m or not m.get("matched"):
            m = fallback_fuzzy_match(src_name, src_site, target_df, tgt_map, config.fuzzy_threshold)

        results.append({
            "source_name": src_name,
            "source_id": src_id,
            "site": src_site,
            "matched": m.get("matched", False),
            "match_type": m.get("match_type", "no_match"),
            "confidence": m.get("confidence", 0.0),
            "reason": m.get("reason", ""),
        })

    return pd.DataFrame(results) if results else pd.DataFrame()


# ============================================================
# MODULE 5 — ESI ELIGIBILITY VALIDATION
# ============================================================


def check_joining_date(row: Dict, col_map: Dict) -> Optional[Dict]:
    doj_col = col_map.get("joining_date")
    if not doj_col:
        return None
    doj_raw = row.get(doj_col)
    if pd.isna(doj_raw):
        return None
    try:
        doj = pd.to_datetime(doj_raw)
        today = pd.Timestamp.now()
        if doj > today:
            return {"issue": "future_joining_date", "severity": "medium",
                    "detail": f"Joining date {doj.date()} is in the future"}
        # If joined mid-month, ESI may need proration
        if doj.day > 15:
            return {"issue": "mid_month_joining", "severity": "info",
                    "detail": f"Joined on {doj.date()} (mid-month) — verify ESI proration"}
    except Exception:
        return {"issue": "invalid_joining_date", "severity": "medium",
                "detail": f"Cannot parse: {doj_raw}"}
    return None


def check_exit_date(row: Dict, col_map: Dict) -> Optional[Dict]:
    doe_col = col_map.get("exit_date")
    doj_col = col_map.get("joining_date")
    if not doe_col:
        return None
    doe_raw = row.get(doe_col)
    if pd.isna(doe_raw):
        return None
    try:
        doe = pd.to_datetime(doe_raw)
        if doj_col:
            doj_raw = row.get(doj_col)
            if pd.notna(doj_raw):
                doj = pd.to_datetime(doj_raw)
                if doe < doj:
                    return {"issue": "exit_before_joining", "severity": "critical",
                            "detail": f"Exit {doe.date()} before joining {doj.date()}"}
        # If exited before month end, ESI should be prorated
        if doe.day < 28:
            return {"issue": "mid_month_exit", "severity": "info",
                    "detail": f"Exited on {doe.date()} — verify ESI proration"}
    except Exception:
        return {"issue": "invalid_exit_date", "severity": "medium",
                "detail": f"Cannot parse: {doe_raw}"}
    return None


def check_mid_month_salary(row: Dict, col_map: Dict, config: ESIConfig) -> Optional[Dict]:
    """If salary is significantly below normal, may indicate partial month."""
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    if not gross_col:
        return None
    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
    if 0 < gross < config.esi_wage_limit * 0.5:
        return {"issue": "very_low_wages", "severity": "low",
                "detail": f"Gross={gross} — below 50% of ESI limit, verify partial month"}
    return None


def check_rejoining(row: Dict, col_map: Dict) -> Optional[Dict]:
    """Flag if employee has exit date but also current wages (rejoining)."""
    doe_col = col_map.get("exit_date")
    if not doe_col:
        return None
    doe = row.get(doe_col)
    if pd.notna(doe):
        gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
        if gross_col:
            gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
            if gross > 0:
                return {"issue": "possible_rejoining", "severity": "info",
                        "detail": f"Exit date={doe} but wages={gross} — verify rejoining"}
    return None


# ============================================================
# MODULE 6 — CONTRIBUTION VALIDATION
# ============================================================


def calculate_expected_employee(gross: float, config: ESIConfig) -> float:
    if gross > config.esi_wage_limit:
        return 0.0
    return round(gross * config.employee_esi_rate, 2)


def calculate_expected_employer(gross: float, config: ESIConfig) -> float:
    if gross > config.esi_wage_limit:
        return 0.0
    return round(gross * config.employer_esi_rate, 2)


def calculate_variance(actual: float, expected: float) -> float:
    return round(actual - expected, 2)


def calculate_percentage_error(actual: float, expected: float) -> float:
    if expected == 0:
        return 0.0 if actual == 0 else 100.0
    return round(abs((actual - expected) / expected) * 100, 2)


def validate_contribution(
    row: Dict, col_map: Dict, config: ESIConfig,
) -> Dict[str, Any]:
    """Full contribution validation."""
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    emp_col = col_map.get("employee_esi")
    er_col = col_map.get("employer_esi")

    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0 if gross_col else 0
    actual_emp = pd.to_numeric(row.get(emp_col, 0), errors="coerce") or 0 if emp_col else 0
    actual_er = pd.to_numeric(row.get(er_col, 0), errors="coerce") or 0 if er_col else 0

    eligible = gross <= config.esi_wage_limit and gross > 0
    expected_emp = calculate_expected_employee(gross, config) if eligible else 0
    expected_er = calculate_expected_employer(gross, config) if eligible else 0

    emp_var = calculate_variance(actual_emp, expected_emp)
    er_var = calculate_variance(actual_er, expected_er)
    emp_pct_err = calculate_percentage_error(actual_emp, expected_emp)
    er_pct_err = calculate_percentage_error(actual_er, expected_er)

    within_tolerance = (
        abs(emp_var) <= config.tolerance_amount and abs(er_var) <= config.tolerance_amount
    )

    return {
        "gross_wages": gross,
        "eligible": eligible,
        "expected_employee_esi": expected_emp,
        "actual_employee_esi": actual_emp,
        "employee_variance": emp_var,
        "employee_pct_error": emp_pct_err,
        "expected_employer_esi": expected_er,
        "actual_employer_esi": actual_er,
        "employer_variance": er_var,
        "employer_pct_error": er_pct_err,
        "within_tolerance": within_tolerance,
        "status": "pass" if within_tolerance else "fail",
    }


# ============================================================
# MODULE 7 — COMPLIANCE RULES ENGINE
# ============================================================


def check_missing_employee(wages_df, esi_df, w_map, e_map) -> pd.DataFrame:
    """Employees in wages but not in ESI records."""
    w_name = w_map.get("employee_name")
    e_name = e_map.get("employee_name")
    if not w_name or not e_name:
        return pd.DataFrame()

    esi_names = set(esi_df[e_name].dropna().apply(normalize_name))
    missing = []
    for _, row in wages_df.iterrows():
        name = row.get(w_name)
        if pd.isna(name):
            continue
        norm = normalize_name(name)
        if norm and norm not in esi_names:
            missing.append({"employee_name": str(name), "missing_from": "esi_records",
                            "severity": "high"})
    return pd.DataFrame(missing) if missing else pd.DataFrame()


def check_duplicate_employee(df, col_map) -> pd.DataFrame:
    name_col = col_map.get("employee_name")
    site_col = col_map.get("site_location")
    if not name_col or name_col not in df.columns:
        return pd.DataFrame()

    dups = []
    grouped = df.dropna(subset=[name_col]).groupby(name_col)
    for name, group in grouped:
        if len(group) < 2:
            continue
        if site_col and site_col in df.columns:
            sites = group[site_col].dropna().unique()
            if len(sites) > 1:
                dups.append({"employee_name": str(name), "duplicate_type": "name_multiple_sites",
                             "sites": ", ".join(str(s) for s in sites), "severity": "medium"})
        else:
            dups.append({"employee_name": str(name), "duplicate_type": "duplicate_name",
                         "severity": "medium"})
    return pd.DataFrame(dups) if dups else pd.DataFrame()


def check_duplicate_ip(df, col_map) -> pd.DataFrame:
    ip_col = col_map.get("ip_number")
    name_col = col_map.get("employee_name")
    if not ip_col or ip_col not in df.columns:
        return pd.DataFrame()

    dups = []
    grouped = df.dropna(subset=[ip_col]).groupby(ip_col)
    for ip, group in grouped:
        if len(group) < 2:
            continue
        names = group[name_col].dropna().tolist() if name_col else []
        dups.append({"ip_number": str(ip), "employee_count": len(group),
                      "employee_names": "; ".join(str(n) for n in names[:5]),
                      "severity": "critical"})
    return pd.DataFrame(dups) if dups else pd.DataFrame()


def check_duplicate_bank(df, col_map) -> pd.DataFrame:
    bank_col = col_map.get("bank_account")
    name_col = col_map.get("employee_name")
    if not bank_col or bank_col not in df.columns:
        return pd.DataFrame()

    dups = []
    grouped = df.dropna(subset=[bank_col]).groupby(bank_col)
    for acct, group in grouped:
        if len(group) < 2:
            continue
        names = group[name_col].dropna().tolist() if name_col else []
        dups.append({"bank_account": str(acct), "employee_count": len(group),
                      "employee_names": "; ".join(str(n) for n in names[:5]),
                      "severity": "critical"})
    return pd.DataFrame(dups) if dups else pd.DataFrame()


def check_invalid_ip(df, col_map) -> pd.DataFrame:
    ip_col = col_map.get("ip_number")
    if not ip_col or ip_col not in df.columns:
        return pd.DataFrame()

    IP_PATTERN = re.compile(r"^\d{10,17}$")
    issues = []
    for _, row in df.iterrows():
        ip = row.get(ip_col)
        if pd.notna(ip) and not IP_PATTERN.match(str(ip).strip()):
            name_col = col_map.get("employee_name")
            issues.append({"employee_name": str(row.get(name_col, "")) if name_col else "",
                           "ip_number": str(ip), "issue": "invalid_ip_format", "severity": "high"})
    return pd.DataFrame(issues) if issues else pd.DataFrame()


def check_invalid_uan(df, col_map) -> pd.DataFrame:
    uan_col = col_map.get("uan_number")
    if not uan_col or uan_col not in df.columns:
        return pd.DataFrame()

    UAN_PATTERN = re.compile(r"^\d{12}$")
    issues = []
    for _, row in df.iterrows():
        uan = row.get(uan_col)
        if pd.notna(uan) and not UAN_PATTERN.match(str(uan).strip()):
            name_col = col_map.get("employee_name")
            issues.append({"employee_name": str(row.get(name_col, "")) if name_col else "",
                           "uan": str(uan), "issue": "invalid_uan_format", "severity": "medium"})
    return pd.DataFrame(issues) if issues else pd.DataFrame()


def check_invalid_wages(df, col_map, config: ESIConfig) -> pd.DataFrame:
    """Flag wages that seem invalid (zero, negative, or unreasonably high)."""
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    if not gross_col or gross_col not in df.columns:
        return pd.DataFrame()

    issues = []
    for _, row in df.iterrows():
        gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce")
        name_col = col_map.get("employee_name")
        name = str(row.get(name_col, "")) if name_col else ""

        if pd.isna(gross) or gross == 0:
            issues.append({"employee_name": name, "issue": "zero_wages", "severity": "high"})
        elif gross < 0:
            issues.append({"employee_name": name, "issue": "negative_wages", "severity": "critical"})
        elif gross > config.esi_wage_limit * 3:
            issues.append({"employee_name": name, "issue": "excessively_high_wages",
                           "value": float(gross), "severity": "low"})

    return pd.DataFrame(issues) if issues else pd.DataFrame()


# ============================================================
# MODULE 8 — FRAUD DETECTION (8 detectors)
# ============================================================


def detect_duplicate_bank(df, col_map) -> pd.DataFrame:
    return check_duplicate_bank(df, col_map)


def detect_salary_splitting(df, col_map, config: ESIConfig) -> pd.DataFrame:
    """Detect employees whose gross is above ESI limit but basic is exactly at limit (salary splitting)."""
    gross_col = col_map.get("gross_wages")
    basic_col = col_map.get("basic_vda")
    name_col = col_map.get("employee_name")
    if not gross_col or not basic_col:
        return pd.DataFrame()

    flags = []
    for _, row in df.iterrows():
        gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
        basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
        if gross > config.esi_wage_limit and basic == config.esi_wage_limit:
            flags.append({
                "employee_name": str(row.get(name_col, "")) if name_col else "",
                "gross_wages": gross, "basic_wages": basic,
                "issue": "Possible salary splitting to stay under ESI limit",
                "severity": "high",
            })
    return pd.DataFrame(flags) if flags else pd.DataFrame()


def detect_fake_employee(wages_df, esi_df, w_map, e_map) -> pd.DataFrame:
    """Employee in ESI but no wages (potential ghost)."""
    w_name = w_map.get("employee_name")
    e_name = e_map.get("employee_name")
    if not w_name or not e_name:
        return pd.DataFrame()

    wage_names = set(wages_df[w_name].dropna().apply(normalize_name))
    ghosts = []
    for _, row in esi_df.iterrows():
        name = row.get(e_name)
        if pd.isna(name):
            continue
        norm = normalize_name(name)
        if norm and norm not in wage_names:
            ghosts.append({"employee_name": str(name), "issue": "In ESI but not in wages",
                           "severity": "critical"})
    return pd.DataFrame(ghosts) if ghosts else pd.DataFrame()


def detect_salary_inflation(df, col_map) -> pd.DataFrame:
    """Detect unusual salary jumps (>50% increase — needs historical data)."""
    # Placeholder — requires historical data
    return pd.DataFrame()


def detect_zero_attendance_salary(
    wages_df, attendance_df, w_map, a_map, config: ESIConfig,
) -> pd.DataFrame:
    """Salary paid but zero attendance days."""
    if attendance_df is None or attendance_df.empty:
        return pd.DataFrame()

    w_name = w_map.get("employee_name")
    a_name = a_map.get("employee_name")
    a_days = a_map.get("days_worked")
    w_gross = w_map.get("gross_wages") or w_map.get("basic_vda")

    if not w_name or not a_name or not a_days:
        return pd.DataFrame()

    att_index = {}
    for _, row in attendance_df.iterrows():
        n = normalize_name(row.get(a_name, ""))
        if n:
            att_index[n] = pd.to_numeric(row.get(a_days, 0), errors="coerce") or 0

    flags = []
    for _, row in wages_df.iterrows():
        name = str(row.get(w_name, ""))
        norm = normalize_name(name)
        gross = pd.to_numeric(row.get(w_gross, 0), errors="coerce") or 0 if w_gross else 0
        if gross <= 0:
            continue
        att_days = att_index.get(norm)
        if att_days is not None and att_days == 0:
            flags.append({"employee_name": name, "gross_wages": gross,
                          "attendance_days": 0, "issue": "Salary with zero attendance",
                          "severity": "critical"})
    return pd.DataFrame(flags) if flags else pd.DataFrame()


def detect_multiple_ip_numbers(df, col_map) -> pd.DataFrame:
    """Same employee with multiple IP numbers."""
    name_col = col_map.get("employee_name")
    ip_col = col_map.get("ip_number")
    if not name_col or not ip_col:
        return pd.DataFrame()

    flags = []
    grouped = df.dropna(subset=[name_col, ip_col]).groupby(name_col)
    for name, group in grouped:
        ips = group[ip_col].unique()
        if len(ips) > 1:
            flags.append({"employee_name": str(name), "ip_count": len(ips),
                          "ip_numbers": "; ".join(str(i) for i in ips),
                          "issue": "Multiple IP numbers", "severity": "high"})
    return pd.DataFrame(flags) if flags else pd.DataFrame()


def detect_multiple_uan(df, col_map) -> pd.DataFrame:
    """Same employee with multiple UANs."""
    name_col = col_map.get("employee_name")
    uan_col = col_map.get("uan_number")
    if not name_col or not uan_col:
        return pd.DataFrame()

    flags = []
    grouped = df.dropna(subset=[name_col, uan_col]).groupby(name_col)
    for name, group in grouped:
        uans = group[uan_col].unique()
        if len(uans) > 1:
            flags.append({"employee_name": str(name), "uan_count": len(uans),
                          "uan_numbers": "; ".join(str(u) for u in uans),
                          "issue": "Multiple UANs", "severity": "high"})
    return pd.DataFrame(flags) if flags else pd.DataFrame()


def detect_ghost_employee(
    wages_df, esi_df, attendance_df, w_map, e_map, a_map,
) -> pd.DataFrame:
    """Employee in ESI with no attendance and no wages."""
    e_name = e_map.get("employee_name")
    if not e_name:
        return pd.DataFrame()

    wage_names = set()
    w_name = w_map.get("employee_name")
    if w_name:
        wage_names = set(wages_df[w_name].dropna().apply(normalize_name))

    att_names = set()
    a_name = a_map.get("employee_name") if a_map else None
    if attendance_df is not None and a_name:
        att_names = set(attendance_df[a_name].dropna().apply(normalize_name))

    ghosts = []
    for _, row in esi_df.iterrows():
        name = str(row.get(e_name, ""))
        if not name or name in ("nan", ""):
            continue
        norm = normalize_name(name)
        indicators = []
        if norm not in wage_names:
            indicators.append("Not in wages")
        if att_names and norm not in att_names:
            indicators.append("Not in attendance")
        if indicators:
            ghosts.append({"employee_name": name, "indicators": "; ".join(indicators),
                           "indicator_count": len(indicators),
                           "severity": "critical" if len(indicators) >= 2 else "high"})
    return pd.DataFrame(ghosts) if ghosts else pd.DataFrame()


# ============================================================
# MODULE 9 — ATTENDANCE CROSS-VALIDATION
# ============================================================


def compare_attendance_vs_salary(
    wages_row, att_row, w_map, a_map, config,
) -> Optional[ValidationResult]:
    w_days = pd.to_numeric(wages_row.get(w_map.get("days_worked", ""), 0), errors="coerce") or 0
    a_days = pd.to_numeric(att_row.get(a_map.get("days_worked", ""), 0), errors="coerce") or 0
    if w_days == 0 and a_days == 0:
        return None
    diff = abs(w_days - a_days)
    if diff <= 1:
        return None
    name = str(wages_row.get(w_map.get("employee_name", ""), ""))
    return ValidationResult(
        employee_name=name, validation_type="attendance_vs_salary",
        expected_value=a_days, actual_value=w_days,
        difference=w_days - a_days,
        status="fail" if diff > 3 else "warning",
        severity="medium" if diff > 3 else "low",
        detail=f"Wage days={w_days}, Attendance days={a_days}",
    )


def compare_ot_vs_attendance(
    wages_row, att_row, w_map, a_map,
) -> Optional[ValidationResult]:
    w_ot = pd.to_numeric(wages_row.get(w_map.get("overtime_amount", ""), 0), errors="coerce") or 0
    a_ot = pd.to_numeric(att_row.get(a_map.get("overtime_amount", ""), 0), errors="coerce") or 0
    if w_ot == 0 and a_ot == 0:
        return None
    diff = abs(w_ot - a_ot)
    if diff <= 10:
        return None
    name = str(wages_row.get(w_map.get("employee_name", ""), ""))
    return ValidationResult(
        employee_name=name, validation_type="ot_vs_attendance",
        expected_value=a_ot, actual_value=w_ot, difference=round(w_ot - a_ot, 2),
        status="warning", severity="low",
        detail=f"Wage OT={w_ot}, Attendance OT={a_ot}",
    )


def compare_leave_vs_salary(
    wages_row, col_map, config,
) -> Optional[ValidationResult]:
    lwp_col = col_map.get("leave_without_pay")
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    if not lwp_col or not gross_col:
        return None
    lwp = pd.to_numeric(wages_row.get(lwp_col, 0), errors="coerce") or 0
    if lwp <= 0:
        return None
    gross = pd.to_numeric(wages_row.get(gross_col, 0), errors="coerce") or 0
    if gross > config.esi_wage_limit:
        return None
    name = str(wages_row.get(col_map.get("employee_name", ""), ""))
    return ValidationResult(
        employee_name=name, validation_type="leave_vs_salary",
        actual_value=lwp, status="info", severity="info",
        detail=f"LWP={lwp}, Gross={gross} — verify ESI proration",
    )


def compare_absent_vs_payment(
    wages_row, att_row, w_map, a_map,
) -> Optional[ValidationResult]:
    a_days = pd.to_numeric(att_row.get(a_map.get("days_worked", ""), 0), errors="coerce") or 0
    gross = pd.to_numeric(wages_row.get(w_map.get("gross_wages", "") or w_map.get("basic_vda", ""), 0), errors="coerce") or 0
    if a_days == 0 and gross > 0:
        name = str(wages_row.get(w_map.get("employee_name", ""), ""))
        return ValidationResult(
            employee_name=name, validation_type="absent_vs_payment",
            expected_value=0, actual_value=gross, difference=gross,
            status="fail", severity="critical",
            detail=f"Zero attendance but gross={gross}",
        )
    return None


# ============================================================
# MODULE 10 — WAGE REGISTER VALIDATION
# ============================================================


def validate_basic(row, col_map) -> Optional[ValidationResult]:
    basic_col = col_map.get("basic_vda")
    if not basic_col:
        return None
    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce")
    if pd.isna(basic) or basic <= 0:
        name = str(row.get(col_map.get("employee_name", ""), ""))
        return ValidationResult(employee_name=name, validation_type="basic_validation",
                                status="fail", severity="high", detail=f"Invalid basic: {basic}")
    # Check minimum wages (approximate ₹178/day for 2024)
    if basic < 4500:
        name = str(row.get(col_map.get("employee_name", ""), ""))
        return ValidationResult(employee_name=name, validation_type="basic_validation",
                                actual_value=float(basic), status="warning", severity="medium",
                                detail=f"Basic={basic} appears below minimum wage")
    return None


def validate_da(row, col_map) -> Optional[ValidationResult]:
    da_col = col_map.get("da")
    if not da_col or da_col not in row.index if hasattr(row, 'index') else da_col not in row:
        return None
    return None  # DA validation — present or not


def validate_ot(row, col_map) -> Optional[ValidationResult]:
    ot_col = col_map.get("overtime_amount")
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    if not ot_col or not gross_col:
        return None
    ot = pd.to_numeric(row.get(ot_col, 0), errors="coerce") or 0
    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
    if ot > 0 and gross > 0 and ot / gross > 0.5:
        name = str(row.get(col_map.get("employee_name", ""), ""))
        return ValidationResult(employee_name=name, validation_type="ot_validation",
                                actual_value=ot, status="warning", severity="medium",
                                detail=f"OT={ot} is >50% of gross={gross}")
    return None


def validate_bonus(row, col_map) -> Optional[ValidationResult]:
    return None  # Bonus included in ESI wages if paid


def validate_total(row, col_map) -> Optional[ValidationResult]:
    """Check if gross = basic + DA + OT + other components."""
    return None  # Requires component-level data


def validate_net_pay(row, col_map) -> Optional[ValidationResult]:
    net_col = col_map.get("net_pay")
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    if not net_col or not gross_col:
        return None
    net = pd.to_numeric(row.get(net_col, 0), errors="coerce") or 0
    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
    if gross > 0 and net > gross:
        name = str(row.get(col_map.get("employee_name", ""), ""))
        return ValidationResult(employee_name=name, validation_type="net_pay_validation",
                                expected_value=gross, actual_value=net, status="fail", severity="high",
                                detail=f"Net pay={net} exceeds gross={gross}")
    return None


# ============================================================
# MODULE 11 — BANK VALIDATION
# ============================================================


def match_bank_transfer(wages_row, bank_row, w_map, b_map) -> Optional[ValidationResult]:
    net_col = w_map.get("net_pay")
    credit_col = b_map.get("transfer_amount") or b_map.get("net_pay")
    if not net_col or not credit_col:
        return None
    net = pd.to_numeric(wages_row.get(net_col, 0), errors="coerce") or 0
    credit = pd.to_numeric(bank_row.get(credit_col, 0), errors="coerce") or 0
    if net == 0 and credit == 0:
        return None
    diff = abs(net - credit)
    if diff <= 5:
        return None
    name = str(wages_row.get(w_map.get("employee_name", ""), ""))
    return ValidationResult(employee_name=name, validation_type="bank_transfer",
                            expected_value=net, actual_value=credit, difference=round(net - credit, 2),
                            status="fail" if diff > 100 else "warning",
                            severity="high" if diff > 100 else "medium",
                            detail=f"Net pay={net}, Bank credit={credit}")


def missing_bank_payment(wages_df, bank_df, w_map, b_map) -> pd.DataFrame:
    w_name = w_map.get("employee_name")
    b_name = b_map.get("employee_name")
    if not w_name or not b_name:
        return pd.DataFrame()

    bank_names = set(bank_df[b_name].dropna().apply(normalize_name))
    missing = []
    for _, row in wages_df.iterrows():
        name = str(row.get(w_name, ""))
        norm = normalize_name(name)
        if norm and norm not in bank_names:
            missing.append({"employee_name": name, "issue": "No bank payment record", "severity": "high"})
    return pd.DataFrame(missing) if missing else pd.DataFrame()


def duplicate_bank_payment(bank_df, b_map) -> pd.DataFrame:
    bank_col = b_map.get("bank_account")
    date_col = b_map.get("transfer_date")
    if not bank_col or bank_col not in bank_df.columns:
        return pd.DataFrame()

    dups = []
    if date_col and date_col in bank_df.columns:
        grouped = bank_df.groupby([bank_col, date_col])
    else:
        grouped = bank_df.groupby(bank_col)

    for key, group in grouped:
        if len(group) > 1:
            dups.append({"key": str(key), "count": len(group),
                         "issue": "Duplicate bank payment", "severity": "high"})
    return pd.DataFrame(dups) if dups else pd.DataFrame()


def partial_payment(wages_df, bank_df, w_map, b_map) -> pd.DataFrame:
    """Detect partial salary payments."""
    w_name = w_map.get("employee_name")
    b_name = b_map.get("employee_name")
    net_col = w_map.get("net_pay")
    credit_col = b_map.get("transfer_amount") or b_map.get("net_pay")

    if not w_name or not b_name or not net_col or not credit_col:
        return pd.DataFrame()

    bank_index = {}
    for _, row in bank_df.iterrows():
        n = normalize_name(row.get(b_name, ""))
        if n:
            bank_index[n] = pd.to_numeric(row.get(credit_col, 0), errors="coerce") or 0

    partials = []
    for _, row in wages_df.iterrows():
        name = str(row.get(w_name, ""))
        norm = normalize_name(name)
        net = pd.to_numeric(row.get(net_col, 0), errors="coerce") or 0
        credit = bank_index.get(norm)
        if credit is not None and net > 0 and 0 < credit < net * 0.9:
            partials.append({"employee_name": name, "expected": net, "paid": credit,
                             "shortfall": round(net - credit, 2), "issue": "Partial payment",
                             "severity": "high"})
    return pd.DataFrame(partials) if partials else pd.DataFrame()


# ============================================================
# MODULE 12 — RISK SCORING ENGINE
# ============================================================


def calculate_risk_score(
    esi_diff: float = 0.0,
    employer_diff: float = 0.0,
    match_confidence: float = 100.0,
    is_duplicate: bool = False,
    missing_count: int = 0,
    fraud_count: int = 0,
    validations_failed: int = 0,
    is_ghost: bool = False,
) -> int:
    score = 0

    # ESI difference (0-25)
    d = abs(esi_diff)
    if d > 500:
        score += 25
    elif d > 200:
        score += 15
    elif d > 50:
        score += 8

    # Employer difference (0-15)
    ed = abs(employer_diff)
    if ed > 500:
        score += 15
    elif ed > 100:
        score += 8

    # Match confidence (0-20)
    if match_confidence < 70:
        score += 20
    elif match_confidence < 80:
        score += 12
    elif match_confidence < 90:
        score += 5

    # Duplicate (0-10)
    if is_duplicate:
        score += 10

    # Missing (0-10)
    score += min(missing_count * 5, 10)

    # Fraud (0-10)
    score += min(fraud_count * 5, 10)

    # Ghost (0-10)
    if is_ghost:
        score += 10

    # Failed validations (0-10)
    score += min(validations_failed * 3, 10)

    return min(score, 100)


def calculate_confidence(risk_score: int) -> float:
    return round(100.0 - risk_score, 1)


def classify_risk(score: int) -> str:
    if score <= 20:
        return RiskLevel.SAFE.value
    elif score <= 40:
        return RiskLevel.LOW.value
    elif score <= 60:
        return RiskLevel.MEDIUM.value
    elif score <= 80:
        return RiskLevel.HIGH.value
    return RiskLevel.CRITICAL.value


# ============================================================
# MODULE 13 — AI RECOMMENDATION ENGINE
# ============================================================


def generate_recommendation(
    employee_name: str,
    issue_type: str,
    detail: str,
    estimated_impact: float = 0.0,
) -> Recommendation:
    """Generate actionable recommendation based on issue type."""
    rules = {
        "esi_above_threshold": {
            "reason": "ESI deducted above wage threshold",
            "suggestion": "Remove ESI deduction — employee wages exceed ₹21,000",
            "priority": "high", "department": "payroll",
        },
        "missing_esi": {
            "reason": "ESI not deducted for eligible employee",
            "suggestion": "Add ESI deduction for current month and check arrears",
            "priority": "high", "department": "payroll",
        },
        "wrong_employee_esi": {
            "reason": "Employee ESI contribution incorrect",
            "suggestion": "Recalculate: Gross × 0.75%. Correct in next payroll.",
            "priority": "high", "department": "payroll",
        },
        "wrong_employer_esi": {
            "reason": "Employer ESI contribution incorrect",
            "suggestion": "Recalculate: Gross × 3.25%. File revised return.",
            "priority": "high", "department": "finance",
        },
        "duplicate_ip": {
            "reason": "Same IP number used for multiple employees",
            "suggestion": "Verify IP assignment. Each employee needs unique IP number.",
            "priority": "critical", "department": "compliance",
        },
        "ghost_employee": {
            "reason": "Employee in ESI with no attendance/wages",
            "suggestion": "Verify employment status. May be ghost employee.",
            "priority": "critical", "department": "hr",
        },
        "salary_splitting": {
            "reason": "Possible salary restructuring to avoid ESI",
            "suggestion": "Audit salary structure. ESI on gross, not just basic.",
            "priority": "high", "department": "compliance",
        },
        "zero_attendance_salary": {
            "reason": "Salary paid with zero attendance",
            "suggestion": "Verify attendance records. May indicate data entry error.",
            "priority": "high", "department": "hr",
        },
        "bank_mismatch": {
            "reason": "Bank transfer doesn't match net pay",
            "suggestion": "Reconcile with bank statement. Verify payment processing.",
            "priority": "medium", "department": "finance",
        },
        "missing_bank": {
            "reason": "No bank payment record found",
            "suggestion": "Verify if salary was paid in cash or payment failed.",
            "priority": "medium", "department": "finance",
        },
    }

    rule = rules.get(issue_type, {
        "reason": detail,
        "suggestion": "Manual review required",
        "priority": "low", "department": "compliance",
    })

    return Recommendation(
        employee_name=employee_name,
        issue_type=issue_type,
        reason=rule["reason"],
        suggestion=rule["suggestion"],
        priority=rule["priority"],
        department=rule["department"],
        estimated_impact=estimated_impact,
    )


def assign_priority(rec: Recommendation) -> str:
    return rec.priority


def assign_department(rec: Recommendation) -> str:
    return rec.department


# ============================================================
# MODULE 14 — AUDIT TRAIL
# ============================================================


def create_audit_log(
    action: str, employee_name: str = "", detail: str = "",
    operator: str = "auto",
):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action=action, employee_name=employee_name,
        detail=detail, operator=operator,
    ))


def log_validation(val: ValidationResult):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action=f"validation_{val.validation_type}",
        employee_name=val.employee_name,
        detail=f"Status={val.status}, Diff={val.difference}, {val.detail}",
    ))


def log_changes(field_name: str, old: str, new: str, employee: str = ""):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="field_change", employee_name=employee,
        field_name=field_name, old_value=old, new_value=new,
    ))


def log_runtime(stats: RuntimeStats):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action="runtime_stats",
        detail=json.dumps(stats.summary(), default=str),
    ))


def log_exception(error_type: str, employee: str, detail: str, severity: str):
    _exception_log.append({
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "employee_name": employee,
        "detail": detail,
        "severity": severity,
    })


def get_audit_dataframe() -> pd.DataFrame:
    return pd.DataFrame([asdict(e) for e in _audit_log]) if _audit_log else pd.DataFrame()


def get_exception_dataframe() -> pd.DataFrame:
    return pd.DataFrame(_exception_log) if _exception_log else pd.DataFrame()


# ============================================================
# MODULE 15-17 — DASHBOARD & SUMMARIES
# ============================================================


def generate_dashboard(
    esi_report: pd.DataFrame,
    match_report: pd.DataFrame,
    validations: List[ValidationResult],
    stats: RuntimeStats,
    fraud_reports: List[pd.DataFrame],
) -> Dict[str, Any]:
    dash = {"generated_at": datetime.now().isoformat(), "engine_version": "4.0.0"}

    if not esi_report.empty and "status" in esi_report.columns:
        total = len(esi_report)
        matched = (esi_report["status"] == "Matched").sum()
        dash["total_employees"] = total
        dash["matched"] = int(matched)
        dash["mismatched"] = int(total - matched)
        dash["compliance_pct"] = round((matched / total * 100) if total else 0, 2)

        if "esi_eligibility" in esi_report.columns:
            dash["esi_applicable"] = int((esi_report["esi_eligibility"] == "Applicable").sum())
            dash["esi_not_applicable"] = int((esi_report["esi_eligibility"] == "Not Applicable").sum())

        if "employee_esi_diff" in esi_report.columns:
            dash["total_employee_esi_diff"] = round(float(esi_report["employee_esi_diff"].sum()), 2)
            dash["total_employer_esi_diff"] = round(float(esi_report["employer_esi_diff"].sum()), 2)

    # Validation stats
    total_v = len(validations)
    passed = sum(1 for v in validations if v.status == "pass")
    dash["validations_run"] = total_v
    dash["validations_passed"] = passed
    dash["validations_failed"] = total_v - passed

    # Fraud flags
    total_fraud = sum(len(f) for f in fraud_reports if f is not None and not f.empty)
    dash["fraud_flags"] = total_fraud

    # Risk distribution
    risk_dist = {}
    for v in validations:
        if v.severity:
            risk_dist[v.severity] = risk_dist.get(v.severity, 0) + 1
    dash["risk_distribution"] = risk_dist

    dash["runtime"] = stats.summary()
    return dash


def generate_site_summary(site_frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    summaries = []
    for site, df in site_frames.items():
        if df.empty:
            continue
        total = len(df)
        matched = (df["status"] == "Matched").sum() if "status" in df.columns else 0
        summaries.append({
            "site": site, "total_employees": total,
            "matched": int(matched), "mismatched": int(total - matched),
            "compliance_pct": round((matched / total * 100) if total else 0, 2),
            "total_esi_diff": round(float(df["employee_esi_diff"].sum()), 2)
            if "employee_esi_diff" in df.columns else 0,
        })
    return pd.DataFrame(summaries) if summaries else pd.DataFrame()


def generate_client_summary(
    client_config: ClientConfig,
    site_summary: pd.DataFrame,
    dashboard: Dict,
) -> Dict[str, Any]:
    return {
        "client_name": client_config.client_name,
        "client_id": client_config.client_id,
        "sites_processed": len(site_summary) if not site_summary.empty else 0,
        "overall_compliance": dashboard.get("compliance_pct", 0),
        "total_employees": dashboard.get("total_employees", 0),
        "total_esi_difference": dashboard.get("total_employee_esi_diff", 0),
    }


# ============================================================
# MODULE 18 — EXCEPTION REPORT
# ============================================================


def generate_exception_report(
    validations: List[ValidationResult],
    fraud_reports: List[pd.DataFrame],
) -> pd.DataFrame:
    frames = []

    # Failed validations
    failed = [asdict(v) for v in validations if v.status in ("fail", "warning")]
    if failed:
        frames.append(pd.DataFrame(failed))

    # Fraud flags
    for fr in fraud_reports:
        if fr is not None and not fr.empty:
            frames.append(fr)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


# ============================================================
# MODULE 23 — AI FEATURES (ANOMALY DETECTION)
# ============================================================


def detect_anomalies_isolation_forest(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    """Detect wage anomalies using statistical outlier detection (no sklearn dependency)."""
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    name_col = col_map.get("employee_name")
    if not gross_col or gross_col not in df.columns:
        return pd.DataFrame()

    values = pd.to_numeric(df[gross_col], errors="coerce").dropna()
    if len(values) < 10:
        return pd.DataFrame()

    mean = values.mean()
    std = values.std()
    if std == 0:
        return pd.DataFrame()

    anomalies = []
    for idx, val in values.items():
        z_score = abs((val - mean) / std)
        if z_score > 3:  # 3-sigma rule
            name = str(df.loc[idx].get(name_col, "")) if name_col else ""
            anomalies.append({
                "employee_name": name, "value": float(val),
                "z_score": round(z_score, 2), "mean": round(mean, 2),
                "std": round(std, 2), "anomaly_type": "statistical_outlier",
                "severity": "high" if z_score > 4 else "medium",
            })

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


def detect_wage_clustering_anomalies(df: pd.DataFrame, col_map: Dict, config: ESIConfig) -> pd.DataFrame:
    """Detect suspicious clustering at ESI threshold."""
    gross_col = col_map.get("gross_wages") or col_map.get("basic_vda")
    name_col = col_map.get("employee_name")
    if not gross_col or gross_col not in df.columns:
        return pd.DataFrame()

    values = pd.to_numeric(df[gross_col], errors="coerce").dropna()
    threshold = config.esi_wage_limit

    # Count employees within ₹500 of threshold
    near_threshold = values[(values >= threshold - 500) & (values <= threshold)]
    pct_near = len(near_threshold) / len(values) * 100 if len(values) > 0 else 0

    if pct_near > 30 and len(values) > 20:
        return pd.DataFrame([{
            "anomaly_type": "threshold_clustering",
            "count": len(near_threshold),
            "percentage": round(pct_near, 1),
            "threshold": threshold,
            "detail": f"{pct_near:.0f}% of employees within ₹500 of ESI limit — possible manipulation",
            "severity": "high",
        }])

    return pd.DataFrame()


# ============================================================
# MODULE 21 — PERFORMANCE STATISTICS
# ============================================================


def processing_time(stats: RuntimeStats) -> float:
    return stats.elapsed


def records_processed(stats: RuntimeStats) -> int:
    return stats.rows_loaded


def error_count(stats: RuntimeStats) -> int:
    return stats.errors


def warning_count(stats: RuntimeStats) -> int:
    return stats.warnings


# ============================================================
# MODULE 19-20 — EXPORT FUNCTIONS
# ============================================================


def export_csv_reports(reports: Dict[str, pd.DataFrame]):
    for name, df in reports.items():
        if df is not None and not df.empty:
            path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            logger.info(f"CSV → {path} ({len(df)} rows)")


def export_excel(reports: Dict[str, pd.DataFrame]):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"esi_reconciliation_{ts}.xlsx"
    sheets = {k[:31]: v for k, v in reports.items() if v is not None and not v.empty}
    if not sheets:
        return
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sn, df in sheets.items():
            df.to_excel(writer, sheet_name=sn, index=False)
    logger.info(f"Excel → {path} ({len(sheets)} sheets)")


def export_json(dashboard: Dict, stats: RuntimeStats):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = {**dashboard, "runtime_stats": stats.summary()}
    path = SUMMARY_DIR / f"esi_summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"JSON → {path}")


def export_api_response(dashboard: Dict) -> str:
    """Return JSON string for API consumption."""
    return json.dumps(dashboard, indent=2, default=str)


# ============================================================
# DATA LOADING
# ============================================================


def load_csv(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        logger.warning(f"Missing file: {file_path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="latin-1")
    if df.empty:
        return df
    df.columns = [str(c).strip().lower().replace("\n", " ") for c in df.columns]
    df = df.dropna(how="all").dropna(axis=1, how="all")
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})
    logger.info(f"Loaded {file_path.name}: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


def load_all_sources(client_config: ClientConfig) -> Dict[str, pd.DataFrame]:
    sources = {}
    files = {
        "wages": INPUT_DIR / client_config.wages_file,
        "esi": INPUT_DIR / client_config.esi_file,
        "bank": INPUT_DIR / client_config.bank_file,
        "attendance": INPUT_DIR / client_config.attendance_file,
        "master": INPUT_DIR / client_config.master_file,
    }
    for key, path in files.items():
        df = load_csv(path)
        if not df.empty:
            sources[key] = df
    return sources


# ============================================================
# MAIN ENGINE
# ============================================================


class ESIReconciliationEngine:
    """
    Production ESI reconciliation orchestrator.
    Runs 23 modules in sequence.
    """

    def __init__(
        self,
        config: Optional[ESIConfig] = None,
        client_name: str = "default",
    ):
        self.config = config or ESIConfig()
        self.client_config = load_client_config(client_name)
        if config:
            self.client_config.esi_config = config
        self.rules = load_rules(self.client_config.esi_config)
        self.stats = RuntimeStats()

        self.sources: Dict[str, pd.DataFrame] = {}
        self.col_maps: Dict[str, Dict[str, Optional[str]]] = {}

        self.esi_report = pd.DataFrame()
        self.match_report = pd.DataFrame()
        self.validations: List[ValidationResult] = []
        self.fraud_reports: List[pd.DataFrame] = []
        self.site_frames: Dict[str, pd.DataFrame] = {}
        self.monthly_results: Dict[str, pd.DataFrame] = {}
        self.recommendations: List[Recommendation] = []

        # Reset global stores
        _audit_log.clear()
        _exception_log.clear()
        _recommendations.clear()

    def run(self) -> Dict[str, Any]:
        self.stats = RuntimeStats()
        cfg = self.client_config.esi_config

        logger.info("=" * 70)
        logger.info("ESI RECONCILIATION ENGINE")
        logger.info(f"Client: {self.client_config.client_name}")
        logger.info(f"ESI Wage Limit: ₹{cfg.esi_wage_limit:,.0f}")
        logger.info(f"Employee Rate: {cfg.employee_esi_rate:.2%}")
        logger.info(f"Employer Rate: {cfg.employer_esi_rate:.2%}")
        logger.info("=" * 70)

        # ── 1. Load data ──
        self.sources = load_all_sources(self.client_config)
        self.stats.files_loaded = len(self.sources)
        for k, df in self.sources.items():
            self.col_maps[k] = build_column_map(df)
            self.stats.rows_loaded += len(df)

        if "wages" not in self.sources:
            logger.error("No wages data — aborting")
            self.stats.finish()
            return {"error": "No wages data"}

        wages_df = self.sources["wages"]
        w_map = self.col_maps["wages"]
        esi_df = self.sources.get("esi", pd.DataFrame())
        e_map = self.col_maps.get("esi", {})
        bank_df = self.sources.get("bank", pd.DataFrame())
        b_map = self.col_maps.get("bank", {})
        att_df = self.sources.get("attendance", pd.DataFrame())
        a_map = self.col_maps.get("attendance", {})

        create_audit_log("ENGINE_START", detail=f"Client={self.client_config.client_name}")

        # ── 2. Input validation ──
        logger.info("PHASE 1: INPUT VALIDATION")
        w_validation = run_input_validation(wages_df, w_map, "wages")
        if not esi_df.empty:
            run_input_validation(esi_df, e_map, "esi")

        # ── 3. Employee matching ──
        logger.info("PHASE 2: EMPLOYEE MATCHING")
        if not esi_df.empty:
            self.match_report = cascade_match_employees(
                wages_df, esi_df, w_map, e_map, cfg
            )
            self.stats.matches_attempted = len(self.match_report)
            if "matched" in self.match_report.columns:
                self.stats.matches_found = int(self.match_report["matched"].sum())
                self.stats.exact_matches = int(
                    self.match_report["match_type"].str.startswith("exact").sum()
                )
                self.stats.fuzzy_matches = int(
                    self.match_report["match_type"].str.startswith("fuzzy").sum()
                )
            logger.info(f"Matches: {self.stats.matches_found}/{self.stats.matches_attempted}")

        # ── 4. ESI Reconciliation ──
        logger.info("PHASE 3: ESI RECONCILIATION")
        site_col = w_map.get("site_location")
        self.esi_report, self.site_frames = process_all_sites(wages_df, cfg, site_col)
        self.stats.sites_processed = len(self.site_frames)

        # ── 5. Contribution validation ──
        logger.info("PHASE 4: CONTRIBUTION VALIDATION")
        for _, row in wages_df.iterrows():
            rd = row.to_dict()
            result = validate_contribution(rd, w_map, cfg)
            emp_name = str(rd.get(w_map.get("employee_name", ""), ""))

            vr = ValidationResult(
                employee_name=emp_name,
                site=str(rd.get(w_map.get("site_location", ""), "")),
                validation_type="contribution",
                expected_value=result["expected_employee_esi"],
                actual_value=result["actual_employee_esi"],
                difference=result["employee_variance"],
                percentage_error=result["employee_pct_error"],
                status=result["status"],
                severity="low" if result["within_tolerance"] else (
                    "medium" if abs(result["employee_variance"]) < 100 else "high"
                ),
                detail=f"Emp: exp={result['expected_employee_esi']}, act={result['actual_employee_esi']}, "
                       f"Er: exp={result['expected_employer_esi']}, act={result['actual_employer_esi']}",
            )
            self.validations.append(vr)
            self.stats.validations_run += 1
            if vr.status == "pass":
                self.stats.validations_passed += 1
            else:
                self.stats.validations_failed += 1
                log_validation(vr)

        # ── 6. Eligibility checks ──
        logger.info("PHASE 5: ESI ELIGIBILITY CHECKS")
        for _, row in wages_df.iterrows():
            rd = row.to_dict()
            name = str(rd.get(w_map.get("employee_name", ""), ""))

            for check_fn in [check_joining_date, check_exit_date, check_rejoining]:
                issue = check_fn(rd, w_map)
                if issue:
                    self.validations.append(ValidationResult(
                        employee_name=name, validation_type=issue["issue"],
                        status="warning" if issue["severity"] != "critical" else "fail",
                        severity=issue["severity"], detail=issue["detail"],
                    ))
                    self.stats.validations_run += 1
                    self.stats.validations_failed += 1

            issue = check_mid_month_salary(rd, w_map, cfg)
            if issue:
                self.validations.append(ValidationResult(
                    employee_name=name, validation_type=issue["issue"],
                    status="info", severity=issue["severity"], detail=issue["detail"],
                ))

        # ── 7. Wage register validation ──
        logger.info("PHASE 6: WAGE REGISTER VALIDATION")
        for _, row in wages_df.iterrows():
            rd = row.to_dict()
            for vfn in [validate_basic, validate_ot, validate_net_pay]:
                vr = vfn(rd, w_map)
                if vr:
                    self.validations.append(vr)
                    self.stats.validations_run += 1
                    self.stats.validations_failed += 1

        # ── 8. Compliance rules ──
        logger.info("PHASE 7: COMPLIANCE RULES")
        if not esi_df.empty:
            missing = check_missing_employee(wages_df, esi_df, w_map, e_map)
            self.stats.missing_found += len(missing)

            dup_ip = check_duplicate_ip(esi_df, e_map)
            invalid_ip = check_invalid_ip(esi_df, e_map)
            invalid_uan = check_invalid_uan(wages_df, w_map)
            invalid_wages = check_invalid_wages(wages_df, w_map, cfg)

            for df_check in (dup_ip, invalid_ip, invalid_uan, invalid_wages):
                if not df_check.empty:
                    self.stats.duplicates_found += len(df_check)

        dup_employee = check_duplicate_employee(wages_df, w_map)
        dup_bank = check_duplicate_bank(wages_df, w_map)

        # ── 9. Fraud detection ──
        logger.info("PHASE 8: FRAUD DETECTION")

        ghosts = pd.DataFrame()
        if not esi_df.empty:
            ghosts = detect_ghost_employee(wages_df, esi_df, att_df, w_map, e_map, a_map)
        salary_split = detect_salary_splitting(wages_df, w_map, cfg)
        fake = pd.DataFrame()
        if not esi_df.empty:
            fake = detect_fake_employee(wages_df, esi_df, w_map, e_map)
        zero_att = detect_zero_attendance_salary(wages_df, att_df, w_map, a_map, cfg) if not att_df.empty else pd.DataFrame()
        multi_ip = detect_multiple_ip_numbers(wages_df, w_map)
        multi_uan = detect_multiple_uan(wages_df, w_map)
        dup_bank_fraud = detect_duplicate_bank(wages_df, w_map)

        self.fraud_reports = [ghosts, salary_split, fake, zero_att, multi_ip, multi_uan, dup_bank_fraud]
        self.stats.fraud_flags = sum(len(f) for f in self.fraud_reports if f is not None and not f.empty)
        logger.info(f"Fraud flags: {self.stats.fraud_flags}")

        # ── 10. Attendance cross-validation ──
        logger.info("PHASE 9: ATTENDANCE CROSS-VALIDATION")
        if not att_df.empty:
            a_name = a_map.get("employee_name")
            if a_name:
                att_index = {}
                for _, row in att_df.iterrows():
                    n = normalize_name(row.get(a_name, ""))
                    if n:
                        att_index[n] = row.to_dict()

                for _, row in wages_df.iterrows():
                    rd = row.to_dict()
                    norm = normalize_name(rd.get(w_map.get("employee_name", ""), ""))
                    if norm in att_index:
                        vr = compare_attendance_vs_salary(rd, att_index[norm], w_map, a_map, cfg)
                        if vr:
                            self.validations.append(vr)
                            self.stats.validations_run += 1
                            self.stats.validations_failed += 1

                        vr = compare_absent_vs_payment(rd, att_index[norm], w_map, a_map)
                        if vr:
                            self.validations.append(vr)
                            self.stats.validations_run += 1
                            self.stats.validations_failed += 1

        # ── 11. Bank validation ──
        logger.info("PHASE 10: BANK VALIDATION")
        if not bank_df.empty:
            b_name = b_map.get("employee_name")
            if b_name:
                bank_index = {}
                for _, row in bank_df.iterrows():
                    n = normalize_name(row.get(b_name, ""))
                    if n:
                        bank_index[n] = row.to_dict()

                for _, row in wages_df.iterrows():
                    rd = row.to_dict()
                    norm = normalize_name(rd.get(w_map.get("employee_name", ""), ""))
                    if norm in bank_index:
                        vr = match_bank_transfer(rd, bank_index[norm], w_map, b_map)
                        if vr:
                            self.validations.append(vr)
                            self.stats.validations_run += 1
                            self.stats.validations_failed += 1

            missing_bank = missing_bank_payment(wages_df, bank_df, w_map, b_map)
            partial = partial_payment(wages_df, bank_df, w_map, b_map)

        # ── 12. Anomaly detection ──
        logger.info("PHASE 11: AI ANOMALY DETECTION")
        stat_anomalies = detect_anomalies_isolation_forest(wages_df, w_map)
        cluster_anomalies = detect_wage_clustering_anomalies(wages_df, w_map, cfg)

        # ── 13. Risk scoring ──
        logger.info("PHASE 12: RISK SCORING")
        risk_records = []
        name_col = w_map.get("employee_name")

        ghost_names = set()
        if not ghosts.empty and "employee_name" in ghosts.columns:
            ghost_names = set(ghosts["employee_name"].apply(normalize_name))

        dup_names = set()
        for df_d in (dup_employee, dup_bank):
            if df_d is not None and not df_d.empty and "employee_name" in df_d.columns:
                dup_names.update(df_d["employee_name"].apply(normalize_name))

        for _, row in wages_df.iterrows():
            rd = row.to_dict()
            name = str(rd.get(name_col, ""))
            norm = normalize_name(name)

            gross = pd.to_numeric(rd.get(w_map.get("gross_wages", "") or w_map.get("basic_vda", ""), 0), errors="coerce") or 0
            actual_emp = pd.to_numeric(rd.get(w_map.get("employee_esi", ""), 0), errors="coerce") or 0
            expected_emp = round(gross * cfg.employee_esi_rate) if gross <= cfg.esi_wage_limit else 0
            emp_diff = actual_emp - expected_emp

            actual_er = pd.to_numeric(rd.get(w_map.get("employer_esi", ""), 0), errors="coerce") or 0
            expected_er = round(gross * cfg.employer_esi_rate) if gross <= cfg.esi_wage_limit else 0
            er_diff = actual_er - expected_er

            emp_failed = sum(1 for v in self.validations
                            if normalize_name(v.employee_name) == norm and v.status in ("fail", "warning"))

            score = calculate_risk_score(
                esi_diff=emp_diff, employer_diff=er_diff,
                is_duplicate=norm in dup_names,
                fraud_count=1 if norm in ghost_names else 0,
                validations_failed=emp_failed,
                is_ghost=norm in ghost_names,
            )

            risk_records.append({
                "employee_name": name,
                "site": str(rd.get(w_map.get("site_location", ""), "")),
                "risk_score": score,
                "risk_level": classify_risk(score),
                "confidence": calculate_confidence(score),
                "esi_difference": round(emp_diff, 2),
                "employer_difference": round(er_diff, 2),
            })

        risk_df = pd.DataFrame(risk_records) if risk_records else pd.DataFrame()

        # ── 14. Recommendations ──
        logger.info("PHASE 13: AI RECOMMENDATIONS")
        for v in self.validations:
            if v.status in ("fail", "warning"):
                issue_type = v.validation_type
                if "above" in v.detail.lower() or "exceed" in v.detail.lower():
                    issue_type = "esi_above_threshold"
                elif "missing" in v.detail.lower() and "esi" in v.detail.lower():
                    issue_type = "missing_esi"
                elif "ghost" in v.validation_type:
                    issue_type = "ghost_employee"

                rec = generate_recommendation(v.employee_name, issue_type, v.detail, abs(v.difference))
                self.recommendations.append(rec)

        self.stats.recommendations = len(self.recommendations)

        # ── 15. Generate reports ──
        logger.info("PHASE 14: REPORT GENERATION")
        dash = generate_dashboard(self.esi_report, self.match_report, self.validations, self.stats, self.fraud_reports)
        site_summary = generate_site_summary(self.site_frames)
        client_summary = generate_client_summary(self.client_config, site_summary, dash)
        exception_report = generate_exception_report(self.validations, self.fraud_reports)
        review_report = self.esi_report[self.esi_report.get("status", pd.Series()) == "Mismatch"].copy() if "status" in self.esi_report.columns else pd.DataFrame()
        dup_report = pd.concat([df for df in (dup_employee, dup_bank, dup_ip) if df is not None and not df.empty], ignore_index=True) if any(df is not None and not df.empty for df in (dup_employee, dup_bank, dup_ip if 'dup_ip' in dir() else pd.DataFrame())) else pd.DataFrame()
        fraud_combined = pd.concat([f for f in self.fraud_reports if f is not None and not f.empty], ignore_index=True) if any(f is not None and not f.empty for f in self.fraud_reports) else pd.DataFrame()
        rec_df = pd.DataFrame([asdict(r) for r in self.recommendations]) if self.recommendations else pd.DataFrame()

        self.stats.finish()
        log_runtime(self.stats)
        audit_df = get_audit_dataframe()
        exception_log_df = get_exception_dataframe()

        # ── 16. Collect all reports ──
        all_reports = {
            "esi_reconciliation_report": self.esi_report,
            "employee_matching_report": self.match_report,
            "missing_employees": missing if 'missing' in dir() and not missing.empty else pd.DataFrame(),
            "duplicate_report": dup_report,
            "duplicate_bank": dup_bank_fraud if 'dup_bank_fraud' in dir() and not dup_bank_fraud.empty else pd.DataFrame(),
            "manual_review": review_report,
            "fraud_flags": fraud_combined,
            "anomalies_statistical": stat_anomalies,
            "anomalies_clustering": cluster_anomalies,
            "risk_summary": risk_df,
            "recommendations": rec_df,
            "site_summary": site_summary,
            "compliance_dashboard": pd.DataFrame([dash]),
            "exception_report": exception_report,
            "audit_trail": audit_df,
            "exception_log": exception_log_df,
        }
        csv_reports = {k: v for k, v in all_reports.items() if v is not None and not v.empty}

        # ── 17. Export ──
        logger.info("PHASE 15: EXPORT")
        export_csv_reports(csv_reports)
        export_excel(csv_reports)
        export_json(dash, self.stats)

        # ── Final summary ──
        logger.info("=" * 70)
        logger.info("ESI RECONCILIATION COMPLETE")
        logger.info(f"  Elapsed:          {self.stats.elapsed}s")
        logger.info(f"  Files loaded:     {self.stats.files_loaded}")
        logger.info(f"  Rows processed:   {self.stats.rows_loaded}")
        logger.info(f"  Matches:          {self.stats.matches_found}/{self.stats.matches_attempted}")
        logger.info(f"  Validations:      {self.stats.validations_run} "
                     f"({self.stats.validations_passed} pass / {self.stats.validations_failed} fail)")
        logger.info(f"  Fraud flags:      {self.stats.fraud_flags}")
        logger.info(f"  Recommendations:  {self.stats.recommendations}")
        logger.info(f"  Compliance:       {dash.get('compliance_pct', 0)}%")
        logger.info(f"  CSV files:        {len(csv_reports)}")
        logger.info(f"  Speed:            {self.stats.rows_per_sec} rows/sec")
        logger.info("=" * 70)

        return {**dash, "client_summary": client_summary}


# ============================================================
# BACKWARD-COMPATIBLE run()
# ============================================================


def run():
    """Legacy entry point."""
    engine = ESIReconciliationEngine()
    return engine.run()


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ESI Reconciliation Engine")
    parser.add_argument("--client", default="default", help="Client name")
    parser.add_argument("--wages", default=None, help="Wages file path")
    parser.add_argument("--esi", default=None, help="ESI file path")
    parser.add_argument("--wage-limit", type=float, default=21000.0)
    parser.add_argument("--emp-rate", type=float, default=0.0075)
    parser.add_argument("--er-rate", type=float, default=0.0325)
    parser.add_argument("--fuzzy-threshold", type=float, default=0.70)
    parser.add_argument("--operator", default="auto")

    args = parser.parse_args()

    cfg = ESIConfig(
        esi_wage_limit=args.wage_limit,
        employee_esi_rate=args.emp_rate,
        employer_esi_rate=args.er_rate,
        fuzzy_threshold=args.fuzzy_threshold,
        operator=args.operator,
    )

    engine = ESIReconciliationEngine(config=cfg, client_name=args.client)
    result = engine.run()
    print(json.dumps(result, indent=2, default=str))
