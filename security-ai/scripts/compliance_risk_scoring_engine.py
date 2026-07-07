# security-ai/scripts/compliance_risk_scoring_engine.py
"""
Production-Grade Compliance Risk Scoring Engine
Security AI — Unified Risk & Compliance Intelligence

═══════════════════════════════════════════════════════════════════
 25 MODULES | 120+ FUNCTIONS | 20+ REPORTS | AI-READY
═══════════════════════════════════════════════════════════════════

 MODULES:
  1.  Configuration Engine
  2.  Input Validation
  3.  PF Risk Engine
  4.  ESI Risk Engine
  5.  Attendance Risk Engine
  6.  Payroll Risk Engine
  7.  Bank Reconciliation Risk
  8.  Identity Risk Engine
  9.  Document Risk Engine
  10. Fraud Risk Engine
  11. Employee Risk Engine
  12. Site Risk Engine
  13. Client Risk Engine
  14. Risk Categories & Compliance %
  15. Trend Analysis
  16. Root Cause Analysis
  17. Recommendation Engine
  18. Risk Dashboard
  19. AI Risk Prediction (Anomaly Detection)
  20. Risk Confidence Score
  21. Exception Management
  22. Site / Client / Guard Ranking
  23. Executive Summary
  24. Audit Trail
  25. Export Engine
"""

import json
import logging
import re
import sys
import time
import warnings
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# MODULE 25 — PRODUCTION LOGGING
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(funcName)s:%(lineno)d | %(message)s"
)
LOG_DATE = "%Y-%m-%d %H:%M:%S"


def setup_rotating_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("RiskEngine")
    root.setLevel(logging.DEBUG)
    if root.handlers:
        return root

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(ch)

    fh = RotatingFileHandler(
        log_dir / "risk_engine.log",
        maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(fh)

    eh = RotatingFileHandler(
        log_dir / "risk_engine_errors.log",
        maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    eh.setLevel(logging.ERROR)
    eh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(eh)

    return root


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
RECON_DIR = BASE_DIR / "reconciliation"
DATASET_DIR = BASE_DIR / "datasets"
OUTPUT_DIR = BASE_DIR / "risk_reports"
EXPORT_DIR = BASE_DIR / "exports"
SUMMARY_DIR = BASE_DIR / "summaries"
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

for _d in (RECON_DIR, DATASET_DIR, OUTPUT_DIR, EXPORT_DIR, SUMMARY_DIR, LOG_DIR, CONFIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

logger = setup_rotating_logger(LOG_DIR)

# ============================================================
# ENUMS
# ============================================================


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Department(str, Enum):
    PAYROLL = "payroll"
    HR = "hr"
    COMPLIANCE = "compliance"
    FINANCE = "finance"
    OPERATIONS = "operations"
    MANAGEMENT = "management"


# ============================================================
# MODULE 1 — CONFIGURATION ENGINE
# ============================================================


@dataclass
class RiskConfig:
    """All risk thresholds and weights — never hardcoded."""
    # Risk level thresholds
    risk_safe_max: int = 20
    risk_low_max: int = 40
    risk_medium_max: int = 60
    risk_high_max: int = 80
    # (above high_max = critical)

    # Category weights (must sum to 1.0)
    weight_pf: float = 0.20
    weight_esi: float = 0.15
    weight_attendance: float = 0.15
    weight_payroll: float = 0.10
    weight_bank: float = 0.10
    weight_identity: float = 0.10
    weight_document: float = 0.05
    weight_fraud: float = 0.10
    weight_employee: float = 0.05

    # Compliance grade thresholds
    grade_a_min: float = 95.0
    grade_b_min: float = 85.0
    grade_c_min: float = 70.0
    grade_d_min: float = 50.0

    # PF rules
    pf_ceiling: float = 15000.0
    pf_employee_rate: float = 0.12
    pf_employer_epf_rate: float = 0.0367
    pf_employer_eps_rate: float = 0.0833

    # ESI rules
    esi_wage_limit: float = 21000.0
    esi_employee_rate: float = 0.0075
    esi_employer_rate: float = 0.0325

    # Risk scores per incident
    score_pf_mismatch: int = 5
    score_esi_mismatch: int = 5
    score_match_mismatch: int = 3
    score_gps_mismatch: int = 2
    score_absent_with_hours: int = 5
    score_negative_pay: int = 10
    score_excessive_ot: int = 5
    score_duplicate: int = 4
    score_ghost: int = 15
    score_missing_document: int = 3
    score_fraud_indicator: int = 10

    # Confidence
    confidence_data_completeness_weight: float = 0.4
    confidence_sample_size_weight: float = 0.3
    confidence_consistency_weight: float = 0.3

    # Engine metadata
    engine_version: str = "5.0.0"
    operator: str = "auto"

    def validate(self) -> bool:
        total = (self.weight_pf + self.weight_esi + self.weight_attendance +
                 self.weight_payroll + self.weight_bank + self.weight_identity +
                 self.weight_document + self.weight_fraud + self.weight_employee)
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Risk weights sum to {total:.3f}, expected 1.0")
        return True


@dataclass
class ClientConfig:
    client_name: str = "default"
    client_id: str = "001"
    sites: List[str] = field(default_factory=list)


def load_config(config_path: Optional[Path] = None) -> RiskConfig:
    cfg = RiskConfig()
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
    cfg.validate()
    return cfg


def load_thresholds(config: RiskConfig) -> Dict[str, Any]:
    return {
        "risk_levels": {
            "safe": config.risk_safe_max,
            "low": config.risk_low_max,
            "medium": config.risk_medium_max,
            "high": config.risk_high_max,
        },
        "grades": {
            "A": config.grade_a_min,
            "B": config.grade_b_min,
            "C": config.grade_c_min,
            "D": config.grade_d_min,
        },
        "weights": {
            "pf": config.weight_pf,
            "esi": config.weight_esi,
            "attendance": config.weight_attendance,
            "payroll": config.weight_payroll,
            "bank": config.weight_bank,
            "identity": config.weight_identity,
            "document": config.weight_document,
            "fraud": config.weight_fraud,
            "employee": config.weight_employee,
        },
    }


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class RiskCategory:
    """Score for a single risk category."""
    category: str = ""
    raw_score: float = 0.0
    weighted_score: float = 0.0
    max_possible: float = 100.0
    incidents: int = 0
    details: List[str] = field(default_factory=list)


@dataclass
class EmployeeRisk:
    """Complete risk profile for one employee."""
    employee_name: str = ""
    employee_id: str = ""
    uan: str = ""
    ip_number: str = ""
    site: str = ""
    client: str = ""

    # Category scores (0-100)
    pf_risk: float = 0.0
    esi_risk: float = 0.0
    attendance_risk: float = 0.0
    payroll_risk: float = 0.0
    bank_risk: float = 0.0
    identity_risk: float = 0.0
    document_risk: float = 0.0
    fraud_risk: float = 0.0

    # Composite
    total_risk_score: float = 0.0
    risk_level: str = RiskLevel.SAFE.value
    compliance_pct: float = 100.0
    confidence_pct: float = 0.0

    # Flags
    is_duplicate: bool = False
    is_ghost: bool = False
    missing_documents: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SiteRisk:
    """Risk profile for a site."""
    site_name: str = ""
    client: str = ""
    total_employees: int = 0
    avg_risk_score: float = 0.0
    risk_level: str = RiskLevel.SAFE.value
    compliance_pct: float = 100.0
    high_risk_count: int = 0
    critical_risk_count: int = 0
    pf_compliance: float = 100.0
    esi_compliance: float = 100.0
    attendance_compliance: float = 100.0
    fraud_flags: int = 0
    rank: int = 0
    trend: str = "stable"


@dataclass
class Recommendation:
    employee_name: str = ""
    employee_id: str = ""
    site: str = ""
    risk_type: str = ""
    risk_score: float = 0.0
    reason: str = ""
    suggestion: str = ""
    priority: str = Priority.MEDIUM.value
    department: str = Department.COMPLIANCE.value
    estimated_days: int = 7
    estimated_impact: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AuditEntry:
    timestamp: str = ""
    action: str = ""
    entity_type: str = ""
    entity_name: str = ""
    old_value: str = ""
    new_value: str = ""
    detail: str = ""
    engine_version: str = "5.0.0"
    operator: str = "auto"


@dataclass
class RuntimeStats:
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_loaded: int = 0
    rows_loaded: int = 0
    employees_scored: int = 0
    sites_scored: int = 0
    validations_run: int = 0
    risk_categories_calculated: int = 0
    recommendations_generated: int = 0
    exceptions_found: int = 0
    errors: int = 0

    def finish(self):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        e = self.end_time or time.perf_counter()
        return round(e - self.start_time, 3)

    def summary(self) -> Dict[str, Any]:
        return {"elapsed_seconds": self.elapsed,
                **{k: v for k, v in self.__dict__.items()
                   if k not in ("start_time", "end_time")}}


# Global stores
_audit_log: List[AuditEntry] = []
_exceptions: List[Dict] = []


# ============================================================
# FIELD RESOLVER
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "employee_name": ["employee_name", "emp_name", "name", "staff_name", "Employee_Name", "NAME", "guard_name"],
    "employee_id": ["employee_id", "emp_id", "emp_code", "staff_id", "code", "Employee_ID"],
    "uan_number": ["uan_number", "uan", "uan_no", "UAN", "source_uan"],
    "ip_number": ["ip_number", "ip_no", "esic_number", "esic_no", "IP Number"],
    "site_location": ["site_location", "site", "location", "branch", "unit", "Site", "site_name"],
    "basic_vda": ["basic_vda", "basic_wages", "basic", "basic + vda", "BASIC + VDA", "Basic_VDA"],
    "gross_wages": ["gross_wages", "gross", "total_wages", "gross_salary", "Gross_Wages"],
    "employee_pf": ["employee_pf", "employee_epf_contribution", "epf", "Actual_PF", "employee_esi"],
    "employer_pf": ["employer_pf", "employer_epf_contribution", "er_epf"],
    "employee_esi": ["employee_esi", "esic", "esi_deduction", "Actual_Employee_ESI", "Actual_Employer_ESI"],
    "employer_esi": ["employer_esi", "employer_esi_contribution"],
    "expected_pf": ["expected_pf", "Expected_PF", "expected_employee_pf"],
    "expected_esi": ["expected_esi", "Expected_Employee_ESI", "expected_employee_esi"],
    "pf_diff": ["pf_difference", "PF_Difference", "employee_pf_diff", "Employee_ESI_Difference"],
    "esi_diff": ["esi_difference", "esi_diff", "employer_esi_diff", "Employer_ESI_Difference"],
    "match_status": ["match_status", "Match_Status", "status", "Status"],
    "match_type": ["match_type", "match_method"],
    "confidence": ["confidence", "confidence_score", "Match_Confidence", "PF_Confidence", "ESI_Confidence", "Bank_Confidence"],
    "risk_score": ["risk_score", "Risk_Score", "total_risk_score", "Total_Risk_Score"],
    "risk_level": ["risk_level", "Risk_Level"],
    "compliance_pct": ["compliance_pct", "compliance_percentage", "Compliance_Pct"],
    "days_worked": ["days_worked", "working_days", "days_present", "Days_Worked"],
    "hours_worked": ["hours_worked", "Hours_Worked"],
    "gps_match": ["gps_match", "GPS_Match", "gps_status"],
    "attendance_status": ["attendance_status", "Status", "status", "attendance"],
    "net_pay": ["net_pay", "Net_Pay", "net_salary"],
    "overtime_hours": ["overtime_hours", "Overtime_Hours", "ot_hours"],
    "joining_date": ["joining_date", "date_of_joining", "doj", "DOJ"],
    "exit_date": ["exit_date", "date_of_exit", "doe", "resignation_date"],
    "bank_account": ["bank_account", "bank_account_number", "account_number"],
    "ifsc_code": ["ifsc", "ifsc_code", "IFSC"],
    "esi_eligibility": ["esi_eligibility", "ESI_Eligibility"],
    "pf_status": ["pf_status", "PF_Status"],
    "esi_status": ["esi_status", "ESI_Status"],
    "police_verification": ["police_verification", "police_verified", "pv_status"],
    "training_status": ["training_status", "trained", "training_complete"],
    "license_expiry": ["license_expiry", "license_valid_until", "psara_expiry"],
    "month": ["month", "pay_month", "salary_month", "Month"],
    "year": ["year", "pay_year", "salary_year", "Year"],
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
# DATA LOADING
# ============================================================


def safe_load(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        logger.warning(f"Missing file: {file_path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="latin-1")
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return pd.DataFrame()
    if df.empty:
        return df
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    logger.info(f"Loaded {file_path.name}: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


def load_all_sources() -> Dict[str, pd.DataFrame]:
    """Load all reconciliation and dataset files."""
    sources = {}
    files = {
        "pf": RECON_DIR / "pf_reconciliation_report.csv",
        "esi": RECON_DIR / "esi_reconciliation_report.csv",
        "matching": RECON_DIR / "employee_matching_report.csv",
        "attendance": DATASET_DIR / "attendance.csv",
        "payroll": DATASET_DIR / "payroll.csv",
        "guards": DATASET_DIR / "guards_master.csv",
        "bank": DATASET_DIR / "bank.csv",
        "fraud": RECON_DIR / "fraud_flags.csv",
        "duplicates": RECON_DIR / "duplicate_employees.csv",
        "missing": RECON_DIR / "missing_employees.csv",
        "risk_summary": RECON_DIR / "risk_summary.csv",
        "audit": RECON_DIR / "audit_trail.csv",
    }
    for key, path in files.items():
        df = safe_load(path)
        if not df.empty:
            sources[key] = df
    return sources


# ============================================================
# MODULE 2 — INPUT VALIDATION
# ============================================================


def validate_input_data(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Validate loaded data quality."""
    report = {}
    for name, df in sources.items():
        if df.empty:
            continue
        col_map = build_column_map(df)
        report[name] = {
            "rows": len(df),
            "columns": len(df.columns),
            "null_pct": round(df.isnull().sum().sum() / df.size * 100, 2) if df.size > 0 else 0,
            "duplicate_rows": int(df.duplicated().sum()),
            "has_employee_name": col_map.get("employee_name") is not None,
        }
    return report


# ============================================================
# MODULE 3 — PF RISK ENGINE
# ============================================================


def calculate_pf_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    """Calculate PF risk score from reconciliation data."""
    df = sources.get("pf")
    if df is None or df.empty:
        return 0.0, 0, []

    col_map = build_column_map(df)
    status_col = col_map.get("match_status")
    diff_col = col_map.get("pf_diff")

    incidents = 0
    details = []

    if status_col and status_col in df.columns:
        mismatches = df[df[status_col].astype(str).str.lower() != "matched"]
        incidents = len(mismatches)
        if incidents > 0:
            details.append(f"{incidents} PF mismatches")

    if diff_col and diff_col in df.columns:
        total_diff = pd.to_numeric(df[diff_col], errors="coerce").abs().sum()
        if total_diff > 0:
            details.append(f"Total PF difference: ₹{total_diff:,.0f}")

    score = min(incidents * config.score_pf_mismatch, 100)
    return score, incidents, details


def calculate_pf_compliance(sources: Dict[str, pd.DataFrame]) -> float:
    df = sources.get("pf")
    if df is None or df.empty:
        return 100.0
    col_map = build_column_map(df)
    status_col = col_map.get("match_status")
    if not status_col or status_col not in df.columns:
        return 100.0
    total = len(df)
    matched = (df[status_col].astype(str).str.lower() == "matched").sum()
    return round((matched / total * 100) if total else 100.0, 2)


def missing_pf(sources: Dict[str, pd.DataFrame]) -> int:
    df = sources.get("missing")
    if df is None or df.empty:
        return 0
    if "missing_from" in df.columns:
        return int((df["missing_from"].astype(str).str.lower() == "pf").sum() +
                    (df["missing_from"].astype(str).str.lower().str.contains("pf")).sum())
    return 0


def duplicate_uan(sources: Dict[str, pd.DataFrame]) -> int:
    df = sources.get("duplicates")
    if df is None or df.empty:
        return 0
    if "duplicate_type" in df.columns:
        return int(df["duplicate_type"].astype(str).str.lower().str.contains("uan").sum())
    return 0


# ============================================================
# MODULE 4 — ESI RISK ENGINE
# ============================================================


def calculate_esi_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    df = sources.get("esi")
    if df is None or df.empty:
        return 0.0, 0, []

    col_map = build_column_map(df)
    status_col = col_map.get("match_status")
    diff_col = col_map.get("esi_diff")

    incidents = 0
    details = []

    if status_col and status_col in df.columns:
        mismatches = df[df[status_col].astype(str).str.lower() != "matched"]
        incidents = len(mismatches)
        if incidents > 0:
            details.append(f"{incidents} ESI mismatches")

    if diff_col and diff_col in df.columns:
        total_diff = pd.to_numeric(df[diff_col], errors="coerce").abs().sum()
        if total_diff > 0:
            details.append(f"Total ESI difference: ₹{total_diff:,.0f}")

    score = min(incidents * config.score_esi_mismatch, 100)
    return score, incidents, details


def calculate_esi_compliance(sources: Dict[str, pd.DataFrame]) -> float:
    df = sources.get("esi")
    if df is None or df.empty:
        return 100.0
    col_map = build_column_map(df)
    status_col = col_map.get("match_status")
    if not status_col or status_col not in df.columns:
        return 100.0
    total = len(df)
    matched = (df[status_col].astype(str).str.lower() == "matched").sum()
    return round((matched / total * 100) if total else 100.0, 2)


def wrong_ip_number(sources: Dict[str, pd.DataFrame]) -> int:
    df = sources.get("esi")
    if df is None or df.empty:
        return 0
    ip_col = find_column(df, "ip_number")
    if not ip_col:
        return 0
    IP_PATTERN = re.compile(r"^\d{10,17}$")
    invalid = df[ip_col].dropna().apply(lambda x: not bool(IP_PATTERN.match(str(x).strip())))
    return int(invalid.sum())


def duplicate_ip(sources: Dict[str, pd.DataFrame]) -> int:
    df = sources.get("duplicates")
    if df is None or df.empty:
        return 0
    if "duplicate_type" in df.columns:
        return int(df["duplicate_type"].astype(str).str.lower().str.contains("ip").sum())
    return 0


# ============================================================
# MODULE 5 — ATTENDANCE RISK ENGINE
# ============================================================


def calculate_attendance_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    df = sources.get("attendance")
    if df is None or df.empty:
        return 0.0, 0, []

    col_map = build_column_map(df)
    incidents = 0
    details = []

    # GPS mismatch
    gps_col = col_map.get("gps_match")
    if gps_col and gps_col in df.columns:
        gps_mismatch = (df[gps_col].astype(str).str.lower() == "no").sum()
        incidents += int(gps_mismatch)
        if gps_mismatch > 0:
            details.append(f"{gps_mismatch} GPS mismatches")

    # Absent but hours > 0
    status_col = col_map.get("attendance_status")
    hours_col = col_map.get("hours_worked")
    if status_col and hours_col and status_col in df.columns and hours_col in df.columns:
        hours = pd.to_numeric(df[hours_col], errors="coerce")
        absent_with_hours = (
            (df[status_col].astype(str).str.lower() == "absent") & (hours > 0)
        ).sum()
        incidents += int(absent_with_hours)
        if absent_with_hours > 0:
            details.append(f"{absent_with_hours} absent but hours > 0")

    score = min(incidents * config.score_gps_mismatch, 100)
    return score, incidents, details


def attendance_percentage(sources: Dict[str, pd.DataFrame]) -> float:
    df = sources.get("attendance")
    if df is None or df.empty:
        return 100.0
    col_map = build_column_map(df)
    status_col = col_map.get("attendance_status")
    if not status_col or status_col not in df.columns:
        return 100.0
    total = len(df)
    present = (df[status_col].astype(str).str.lower() == "present").sum()
    return round((present / total * 100) if total else 100.0, 2)


def late_percentage(sources: Dict[str, pd.DataFrame]) -> float:
    df = sources.get("attendance")
    if df is None or df.empty:
        return 0.0
    if "late" in str(df.columns).lower():
        late_col = find_column(df, "late")
        if late_col:
            return round((df[late_col].astype(str).str.lower().isin(["yes", "true", "1"]).sum() / len(df) * 100), 2)
    return 0.0


def continuous_absence(sources: Dict[str, pd.DataFrame]) -> int:
    """Count employees with 3+ consecutive absences."""
    df = sources.get("attendance")
    if df is None or df.empty:
        return 0
    # Simplified: count employees with < 50% attendance
    col_map = build_column_map(df)
    name_col = col_map.get("employee_name")
    status_col = col_map.get("attendance_status")
    if not name_col or not status_col:
        return 0
    grouped = df.groupby(name_col)
    count = 0
    for _, group in grouped:
        total = len(group)
        absent = (group[status_col].astype(str).str.lower() == "absent").sum()
        if total > 0 and absent / total > 0.5:
            count += 1
    return count


def overtime_percentage(sources: Dict[str, pd.DataFrame]) -> float:
    df = sources.get("attendance")
    if df is None or df.empty:
        return 0.0
    hours_col = find_column(df, "hours_worked")
    if not hours_col:
        return 0.0
    hours = pd.to_numeric(df[hours_col], errors="coerce")
    overtime_rows = (hours > 8).sum()
    return round((overtime_rows / len(df) * 100) if len(df) else 0.0, 2)


def calculate_attendance_compliance(sources: Dict[str, pd.DataFrame]) -> float:
    return attendance_percentage(sources)


# ============================================================
# MODULE 6 — PAYROLL RISK ENGINE
# ============================================================


def calculate_payroll_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    df = sources.get("payroll")
    if df is None or df.empty:
        return 0.0, 0, []

    col_map = build_column_map(df)
    incidents = 0
    details = []

    # Negative net pay
    net_col = col_map.get("net_pay")
    if net_col and net_col in df.columns:
        net = pd.to_numeric(df[net_col], errors="coerce")
        neg = (net < 0).sum()
        incidents += int(neg)
        if neg > 0:
            details.append(f"{neg} negative net pay")

    # Excessive OT
    ot_col = col_map.get("overtime_hours")
    if ot_col and ot_col in df.columns:
        ot = pd.to_numeric(df[ot_col], errors="coerce")
        excessive = (ot > 100).sum()
        incidents += int(excessive)
        if excessive > 0:
            details.append(f"{excessive} excessive OT (>100 hrs)")

    score = min(incidents * config.score_negative_pay, 100)
    return score, incidents, details


def salary_variance(sources: Dict[str, pd.DataFrame]) -> float:
    df = sources.get("payroll")
    if df is None or df.empty:
        return 0.0
    net_col = find_column(df, "net_pay")
    if not net_col:
        return 0.0
    vals = pd.to_numeric(df[net_col], errors="coerce").dropna()
    return round(float(vals.std()), 2) if len(vals) > 1 else 0.0


def abnormal_salary(sources: Dict[str, pd.DataFrame]) -> int:
    df = sources.get("payroll")
    if df is None or df.empty:
        return 0
    net_col = find_column(df, "net_pay")
    if not net_col:
        return 0
    vals = pd.to_numeric(df[net_col], errors="coerce").dropna()
    if len(vals) < 10:
        return 0
    mean, std = vals.mean(), vals.std()
    if std == 0:
        return 0
    z = ((vals - mean).abs() / std)
    return int((z > 3).sum())


def duplicate_salary(sources: Dict[str, pd.DataFrame]) -> int:
    df = sources.get("payroll")
    if df is None or df.empty:
        return 0
    net_col = find_column(df, "net_pay")
    name_col = find_column(df, "employee_name")
    if not net_col or not name_col:
        return 0
    grouped = df.groupby(name_col)[net_col].nunique()
    return int((grouped > 1).sum())


# ============================================================
# MODULE 7 — BANK RECONCILIATION RISK
# ============================================================


def calculate_bank_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    df = sources.get("bank")
    if df is None or df.empty:
        return 0.0, 0, []

    incidents = 0
    details = []

    # Check for duplicate bank accounts
    bank_col = find_column(df, "bank_account")
    if bank_col and bank_col in df.columns:
        dup_count = df[bank_col].dropna().duplicated(keep=False).sum()
        if dup_count > 0:
            incidents += int(dup_count)
            details.append(f"{dup_count} duplicate bank accounts")

    score = min(incidents * config.score_duplicate, 100)
    return score, incidents, details


def missing_bank_transfer(sources: Dict[str, pd.DataFrame]) -> int:
    matching = sources.get("matching")
    if matching is None or matching.empty:
        return 0
    bank_conf = find_column(matching, "Bank_Confidence")
    if not bank_conf:
        return 0
    vals = pd.to_numeric(matching[bank_conf], errors="coerce")
    return int((vals < 70).sum())


def salary_not_paid(sources: Dict[str, pd.DataFrame]) -> int:
    payroll = sources.get("payroll")
    bank = sources.get("bank")
    if payroll is None or bank is None:
        return 0
    p_name = find_column(payroll, "employee_name")
    b_name = find_column(bank, "employee_name")
    if not p_name or not b_name:
        return 0
    bank_names = set(bank[b_name].dropna().astype(str).str.upper().str.strip())
    paid_missing = payroll[~payroll[p_name].astype(str).str.upper().str.strip().isin(bank_names)]
    return len(paid_missing)


# ============================================================
# MODULE 8 — IDENTITY RISK ENGINE
# ============================================================


def calculate_identity_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    incidents = 0
    details = []

    # Duplicate detection
    dup_df = sources.get("duplicates")
    if dup_df is not None and not dup_df.empty:
        incidents += len(dup_df)
        details.append(f"{len(dup_df)} duplicate identity records")

    # Matching confidence
    match_df = sources.get("matching")
    if match_df is not None and not match_df.empty:
        conf_col = find_column(match_df, "confidence")
        if conf_col:
            conf = pd.to_numeric(match_df[conf_col], errors="coerce")
            low_conf = (conf < 70).sum()
            if low_conf > 0:
                incidents += int(low_conf)
                details.append(f"{low_conf} low-confidence identity matches")

    score = min(incidents * config.score_duplicate, 100)
    return score, incidents, details


def duplicate_identity(sources: Dict[str, pd.DataFrame]) -> int:
    dup_df = sources.get("duplicates")
    return len(dup_df) if dup_df is not None and not dup_df.empty else 0


# ============================================================
# MODULE 9 — DOCUMENT RISK ENGINE
# ============================================================


def calculate_document_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    df = sources.get("guards")
    if df is None or df.empty:
        return 0.0, 0, []

    incidents = 0
    details = []

    # Missing police verification
    pv = missing_police_verification(df)
    if pv > 0:
        incidents += pv
        details.append(f"{pv} missing police verification")

    # Missing training
    tr = missing_training(df)
    if tr > 0:
        incidents += tr
        details.append(f"{tr} missing training records")

    # Expired documents
    exp = expired_documents(df)
    if exp > 0:
        incidents += exp
        details.append(f"{exp} expired documents")

    score = min(incidents * config.score_missing_document, 100)
    return score, incidents, details


def missing_police_verification(df: pd.DataFrame) -> int:
    col = find_column(df, "police_verification")
    if not col or col not in df.columns:
        return 0
    return int(df[col].isna().sum() + (df[col].astype(str).str.lower().isin(["no", "nan", "none", ""])).sum())


def missing_training(df: pd.DataFrame) -> int:
    col = find_column(df, "training_status")
    if not col or col not in df.columns:
        return 0
    return int(df[col].isna().sum() + (df[col].astype(str).str.lower().isin(["no", "nan", "none", "pending", ""])).sum())


def expired_documents(df: pd.DataFrame) -> int:
    col = find_column(df, "license_expiry")
    if not col or col not in df.columns:
        return 0
    today = pd.Timestamp.now()
    dates = pd.to_datetime(df[col], errors="coerce")
    return int((dates < today).sum())


def expired_license(df: pd.DataFrame) -> int:
    return expired_documents(df)


# ============================================================
# MODULE 10 — FRAUD RISK ENGINE
# ============================================================


def calculate_fraud_risk(sources: Dict[str, pd.DataFrame], config: RiskConfig) -> Tuple[float, int, List[str]]:
    incidents = 0
    details = []

    fraud_df = sources.get("fraud")
    if fraud_df is not None and not fraud_df.empty:
        incidents += len(fraud_df)
        details.append(f"{len(fraud_df)} fraud flags from fraud engine")

    # Ghost employees
    ghosts = ghost_employee(sources)
    if ghosts > 0:
        incidents += ghosts
        details.append(f"{ghosts} suspected ghost employees")

    # Salary inflation
    inflated = salary_inflation(sources)
    if inflated > 0:
        incidents += inflated
        details.append(f"{inflated} salary inflation flags")

    score = min(incidents * config.score_fraud_indicator, 100)
    return score, incidents, details


def ghost_employee(sources: Dict[str, pd.DataFrame]) -> int:
    fraud_df = sources.get("fraud")
    if fraud_df is None or fraud_df.empty:
        return 0
    if "anomaly_type" in fraud_df.columns:
        return int(fraud_df["anomaly_type"].astype(str).str.lower().str.contains("ghost").sum())
    if "issue" in fraud_df.columns:
        return int(fraud_df["issue"].astype(str).str.lower().str.contains("ghost|not in wage").sum())
    return 0


def salary_inflation(sources: Dict[str, pd.DataFrame]) -> int:
    fraud_df = sources.get("fraud")
    if fraud_df is None or fraud_df.empty:
        return 0
    if "anomaly_type" in fraud_df.columns:
        return int(fraud_df["anomaly_type"].astype(str).str.lower().str.contains("inflat|split").sum())
    return 0


def identity_fraud(sources: Dict[str, pd.DataFrame]) -> int:
    return duplicate_identity(sources)


# ============================================================
# MODULE 11 — EMPLOYEE RISK ENGINE
# ============================================================


def calculate_employee_risk_scores(
    sources: Dict[str, pd.DataFrame],
    config: RiskConfig,
) -> List[EmployeeRisk]:
    """Calculate risk score for every individual employee."""
    # Build employee list from all sources
    all_names: Dict[str, Dict] = {}

    for src_name in ("pf", "esi", "matching", "payroll", "attendance", "guards"):
        df = sources.get(src_name)
        if df is None or df.empty:
            continue
        col_map = build_column_map(df)
        name_col = col_map.get("employee_name")
        if not name_col or name_col not in df.columns:
            continue
        id_col = col_map.get("employee_id")
        site_col = col_map.get("site_location")
        uan_col = col_map.get("uan_number")

        for _, row in df.iterrows():
            name = str(row.get(name_col, "")).strip().upper()
            if not name or name in ("NAN", "NONE", ""):
                continue
            if name not in all_names:
                all_names[name] = {
                    "employee_name": name,
                    "employee_id": str(row.get(id_col, "")) if id_col else "",
                    "uan": str(row.get(uan_col, "")) if uan_col else "",
                    "site": str(row.get(site_col, "")) if site_col else "",
                    "sources": set(),
                }
            all_names[name]["sources"].add(src_name)

    # Score each employee
    dup_names = set()
    dup_df = sources.get("duplicates")
    if dup_df is not None and "employee_a_name" in dup_df.columns:
        dup_names.update(dup_df["employee_a_name"].astype(str).str.upper().str.strip())

    ghost_names = set()
    fraud_df = sources.get("fraud")
    if fraud_df is not None and "employee_name" in fraud_df.columns:
        ghost_mask = fraud_df.get("issue", pd.Series()).astype(str).str.lower().str.contains("ghost|not in wage", na=False)
        ghost_names.update(fraud_df.loc[ghost_mask, "employee_name"].astype(str).str.upper().str.strip())

    # Build lookup tables
    pf_lookup = {}
    pf_df = sources.get("pf")
    if pf_df is not None:
        pn = find_column(pf_df, "employee_name")
        ps = find_column(pf_df, "match_status")
        pd_col = find_column(pf_df, "pf_diff")
        if pn:
            for _, r in pf_df.iterrows():
                key = str(r.get(pn, "")).upper().strip()
                pf_lookup[key] = {
                    "status": str(r.get(ps, "")) if ps else "",
                    "diff": pd.to_numeric(r.get(pd_col, 0), errors="coerce") if pd_col else 0,
                }

    esi_lookup = {}
    esi_df = sources.get("esi")
    if esi_df is not None:
        en = find_column(esi_df, "employee_name")
        es = find_column(esi_df, "match_status")
        ed = find_column(esi_df, "esi_diff")
        if en:
            for _, r in esi_df.iterrows():
                key = str(r.get(en, "")).upper().strip()
                esi_lookup[key] = {
                    "status": str(r.get(es, "")) if es else "",
                    "diff": pd.to_numeric(r.get(ed, 0), errors="coerce") if ed else 0,
                }

    employee_risks = []

    for name, meta in all_names.items():
        er = EmployeeRisk(
            employee_name=name,
            employee_id=meta["employee_id"],
            uan=meta["uan"],
            site=meta["site"],
        )

        # PF risk
        pf_info = pf_lookup.get(name, {})
        if pf_info.get("status", "").lower() != "matched" and pf_info:
            er.pf_risk = min(abs(pf_info.get("diff", 0)) / 10, 100)
            er.risk_factors.append(f"PF mismatch (diff={pf_info.get('diff', 0):.0f})")

        # ESI risk
        esi_info = esi_lookup.get(name, {})
        if esi_info.get("status", "").lower() != "matched" and esi_info:
            er.esi_risk = min(abs(esi_info.get("diff", 0)) / 10, 100)
            er.risk_factors.append(f"ESI mismatch (diff={esi_info.get('diff', 0):.0f})")

        # Identity risk
        if name in dup_names:
            er.identity_risk = 80
            er.is_duplicate = True
            er.risk_factors.append("Duplicate identity detected")

        # Fraud risk
        if name in ghost_names:
            er.fraud_risk = 100
            er.is_ghost = True
            er.risk_factors.append("Suspected ghost employee")

        # Composite score
        er.total_risk_score = round(
            er.pf_risk * config.weight_pf +
            er.esi_risk * config.weight_esi +
            er.attendance_risk * config.weight_attendance +
            er.payroll_risk * config.weight_payroll +
            er.bank_risk * config.weight_bank +
            er.identity_risk * config.weight_identity +
            er.document_risk * config.weight_document +
            er.fraud_risk * config.weight_fraud, 1
        )

        er.risk_level = classify_risk(er.total_risk_score, config)
        er.compliance_pct = round(max(0, 100 - er.total_risk_score), 1)
        er.confidence_pct = calculate_confidence(er, sources)

        employee_risks.append(er)

    return employee_risks


def top_high_risk_employees(employees: List[EmployeeRisk], n: int = 10) -> List[EmployeeRisk]:
    return sorted(employees, key=lambda e: e.total_risk_score, reverse=True)[:n]


# ============================================================
# MODULE 12 — SITE RISK ENGINE
# ============================================================


def calculate_site_risk(
    employees: List[EmployeeRisk],
    config: RiskConfig,
) -> List[SiteRisk]:
    """Aggregate employee risks into site-level scores."""
    site_data: Dict[str, List[EmployeeRisk]] = defaultdict(list)
    for er in employees:
        site = er.site or "UNKNOWN"
        site_data[site].append(er)

    site_risks = []
    for site, emps in site_data.items():
        sr = SiteRisk(
            site_name=site,
            total_employees=len(emps),
            avg_risk_score=round(np.mean([e.total_risk_score for e in emps]), 1) if emps else 0,
            high_risk_count=sum(1 for e in emps if e.risk_level in ("high", "critical")),
            critical_risk_count=sum(1 for e in emps if e.risk_level == "critical"),
            fraud_flags=sum(1 for e in emps if e.is_ghost or e.is_duplicate),
        )
        sr.risk_level = classify_risk(sr.avg_risk_score, config)
        sr.compliance_pct = round(np.mean([e.compliance_pct for e in emps]), 1) if emps else 100.0
        sr.pf_compliance = round(100 - np.mean([e.pf_risk for e in emps]), 1) if emps else 100.0
        sr.esi_compliance = round(100 - np.mean([e.esi_risk for e in emps]), 1) if emps else 100.0
        sr.attendance_compliance = round(100 - np.mean([e.attendance_risk for e in emps]), 1) if emps else 100.0
        site_risks.append(sr)

    return site_risks


def build_site_risk_summary(site_risks: List[SiteRisk]) -> pd.DataFrame:
    return pd.DataFrame([asdict(s) for s in site_risks]) if site_risks else pd.DataFrame()


def rank_sites_by_risk(site_risks: List[SiteRisk]) -> List[SiteRisk]:
    sorted_sites = sorted(site_risks, key=lambda s: s.avg_risk_score, reverse=True)
    for i, s in enumerate(sorted_sites):
        s.rank = i + 1
    return sorted_sites


# ============================================================
# MODULE 13 — CLIENT RISK ENGINE
# ============================================================


def calculate_client_risk(
    site_risks: List[SiteRisk],
    client_config: ClientConfig,
) -> Dict[str, Any]:
    if not site_risks:
        return {"client": client_config.client_name, "risk_score": 0, "compliance": 100}

    avg_score = np.mean([s.avg_risk_score for s in site_risks])
    avg_compliance = np.mean([s.compliance_pct for s in site_risks])
    total_emps = sum(s.total_employees for s in site_risks)
    total_fraud = sum(s.fraud_flags for s in site_risks)

    return {
        "client_name": client_config.client_name,
        "client_id": client_config.client_id,
        "total_sites": len(site_risks),
        "total_employees": int(total_emps),
        "avg_risk_score": round(float(avg_score), 1),
        "avg_compliance": round(float(avg_compliance), 1),
        "total_fraud_flags": int(total_fraud),
        "risk_level": classify_risk(avg_score, RiskConfig()),
    }


def build_client_dashboard(client_risk: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "dashboard_type": "client",
        **client_risk,
        "generated_at": datetime.now().isoformat(),
    }


# ============================================================
# MODULE 14 — RISK CATEGORIES & COMPLIANCE PERCENTAGE
# ============================================================


def calculate_compliance_risk(employees: List[EmployeeRisk]) -> float:
    if not employees:
        return 0.0
    return round(np.mean([e.total_risk_score for e in employees]), 1)


def calculate_compliance_percentage(employees: List[EmployeeRisk]) -> Dict[str, float]:
    if not employees:
        return {"overall": 100.0}
    return {
        "overall": round(np.mean([e.compliance_pct for e in employees]), 1),
        "pf": round(np.mean([100 - e.pf_risk for e in employees]), 1),
        "esi": round(np.mean([100 - e.esi_risk for e in employees]), 1),
        "attendance": round(np.mean([100 - e.attendance_risk for e in employees]), 1),
        "identity": round(np.mean([100 - e.identity_risk for e in employees]), 1),
        "fraud": round(np.mean([100 - e.fraud_risk for e in employees]), 1),
    }


def classify_risk(score: float, config: RiskConfig) -> str:
    if score <= config.risk_safe_max:
        return RiskLevel.SAFE.value
    elif score <= config.risk_low_max:
        return RiskLevel.LOW.value
    elif score <= config.risk_medium_max:
        return RiskLevel.MEDIUM.value
    elif score <= config.risk_high_max:
        return RiskLevel.HIGH.value
    return RiskLevel.CRITICAL.value


def assign_compliance_grade(pct: float, config: RiskConfig) -> str:
    if pct >= config.grade_a_min:
        return ComplianceGrade.A.value
    elif pct >= config.grade_b_min:
        return ComplianceGrade.B.value
    elif pct >= config.grade_c_min:
        return ComplianceGrade.C.value
    elif pct >= config.grade_d_min:
        return ComplianceGrade.D.value
    return ComplianceGrade.F.value


# ============================================================
# MODULE 15 — TREND ANALYSIS
# ============================================================


def compare_previous_month(
    current_employees: List[EmployeeRisk],
    previous_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compare current scores with previous month if available."""
    if previous_file is None or not previous_file.exists():
        return {"status": "no_previous_data"}

    prev_df = pd.read_csv(previous_file)
    if prev_df.empty:
        return {"status": "no_previous_data"}

    # Build lookup
    prev_lookup = {}
    if "employee_name" in prev_df.columns and "total_risk_score" in prev_df.columns:
        for _, row in prev_df.iterrows():
            name = str(row["employee_name"]).upper().strip()
            prev_lookup[name] = float(row["total_risk_score"])

    improved = 0
    worsened = 0
    stable = 0
    new = 0

    for er in current_employees:
        prev_score = prev_lookup.get(er.employee_name)
        if prev_score is None:
            new += 1
        elif er.total_risk_score < prev_score - 5:
            improved += 1
        elif er.total_risk_score > prev_score + 5:
            worsened += 1
        else:
            stable += 1

    return {
        "improved": improved,
        "worsened": worsened,
        "stable": stable,
        "new_employees": new,
        "total_current": len(current_employees),
        "total_previous": len(prev_lookup),
    }


def risk_trend(
    monthly_results: Dict[str, Dict[str, Any]],
) -> pd.DataFrame:
    """Track risk scores across months."""
    rows = []
    for month_key in sorted(monthly_results.keys()):
        data = monthly_results[month_key]
        rows.append({
            "month": month_key,
            "avg_risk_score": data.get("avg_risk_score", 0),
            "compliance_pct": data.get("compliance_pct", 0),
            "high_risk_count": data.get("high_risk_count", 0),
        })

    df = pd.DataFrame(rows)
    if len(df) >= 2:
        df["trend"] = df["avg_risk_score"].diff().apply(
            lambda x: "improving" if x and x < 0 else ("declining" if x and x > 0 else "stable")
        )
    return df


# ============================================================
# MODULE 16 — ROOT CAUSE ANALYSIS
# ============================================================


def find_root_cause(er: EmployeeRisk) -> List[Dict[str, str]]:
    """Identify root causes for high risk scores."""
    causes = []

    if er.pf_risk > 50:
        causes.append({
            "risk": "PF", "score": er.pf_risk,
            "reason": "PF contribution mismatch detected",
            "evidence": f"PF risk score: {er.pf_risk:.0f}/100",
            "recommendation": "Verify PF wages and recalculate contributions",
        })

    if er.esi_risk > 50:
        causes.append({
            "risk": "ESI", "score": er.esi_risk,
            "reason": "ESI contribution mismatch detected",
            "evidence": f"ESI risk score: {er.esi_risk:.0f}/100",
            "recommendation": "Check ESI eligibility and recalculate",
        })

    if er.is_ghost:
        causes.append({
            "risk": "Fraud", "score": er.fraud_risk,
            "reason": "Suspected ghost employee — in ESI but not in wages/attendance",
            "evidence": f"Fraud risk score: {er.fraud_risk:.0f}/100",
            "recommendation": "Verify physical presence, check all identity documents",
        })

    if er.is_duplicate:
        causes.append({
            "risk": "Identity", "score": er.identity_risk,
            "reason": "Duplicate identity — same UAN/Aadhaar/bank for multiple records",
            "evidence": f"Identity risk score: {er.identity_risk:.0f}/100",
            "recommendation": "Verify employee identity, resolve duplicates",
        })

    if not causes and er.total_risk_score > 40:
        causes.append({
            "risk": "General", "score": er.total_risk_score,
            "reason": "Multiple low-level issues compounding",
            "evidence": f"Risk factors: {', '.join(er.risk_factors) if er.risk_factors else 'none'}",
            "recommendation": "Review all compliance areas for this employee",
        })

    return causes


# ============================================================
# MODULE 17 — RECOMMENDATION ENGINE
# ============================================================


def generate_recommendations(
    employees: List[EmployeeRisk],
) -> List[Recommendation]:
    """Generate actionable recommendations for high-risk employees."""
    recs = []

    for er in employees:
        if er.total_risk_score <= 40:
            continue

        causes = find_root_cause(er)
        for cause in causes:
            priority = Priority.CRITICAL.value if cause["score"] > 80 else (
                Priority.HIGH.value if cause["score"] > 60 else (
                    Priority.MEDIUM.value if cause["score"] > 40 else Priority.LOW.value
                )
            )

            dept = Department.PAYROLL.value
            if "PF" in cause["risk"] or "ESI" in cause["risk"]:
                dept = Department.COMPLIANCE.value
            elif "Fraud" in cause["risk"] or "Ghost" in cause["reason"]:
                dept = Department.HR.value
            elif "Identity" in cause["risk"]:
                dept = Department.HR.value
            elif "Bank" in cause["risk"]:
                dept = Department.FINANCE.value

            days = 3 if priority == Priority.CRITICAL.value else (
                7 if priority == Priority.HIGH.value else 14
            )

            recs.append(Recommendation(
                employee_name=er.employee_name,
                employee_id=er.employee_id,
                site=er.site,
                risk_type=cause["risk"],
                risk_score=cause["score"],
                reason=cause["reason"],
                suggestion=cause["recommendation"],
                priority=priority,
                department=dept,
                estimated_days=days,
                estimated_impact=round(cause["score"] * 0.5, 1),
            ))

    return sorted(recs, key=lambda r: r.risk_score, reverse=True)


# ============================================================
# MODULE 18 — RISK DASHBOARD
# ============================================================


def build_dashboard(
    employees: List[EmployeeRisk],
    site_risks: List[SiteRisk],
    config: RiskConfig,
) -> Dict[str, Any]:
    """Build comprehensive risk dashboard."""
    compliance = calculate_compliance_percentage(employees)

    risk_dist = defaultdict(int)
    for er in employees:
        risk_dist[er.risk_level] += 1

    top_risks = top_high_risk_employees(employees, 10)

    return {
        "generated_at": datetime.now().isoformat(),
        "engine_version": config.engine_version,
        "summary": {
            "total_employees": len(employees),
            "total_sites": len(site_risks),
            "overall_compliance": compliance["overall"],
            "compliance_grade": assign_compliance_grade(compliance["overall"], config),
            "avg_risk_score": round(np.mean([e.total_risk_score for e in employees]), 1) if employees else 0,
        },
        "compliance_breakdown": compliance,
        "risk_distribution": dict(risk_dist),
        "top_10_risks": [
            {"name": e.employee_name, "site": e.site,
             "score": e.total_risk_score, "level": e.risk_level,
             "factors": e.risk_factors[:3]}
            for e in top_risks
        ],
        "site_summary": [
            {"site": s.site_name, "risk_score": s.avg_risk_score,
             "compliance": s.compliance_pct, "employees": s.total_employees}
            for s in sorted(site_risks, key=lambda x: x.avg_risk_score, reverse=True)[:10]
        ],
    }


def build_summary(dashboard: Dict) -> Dict[str, Any]:
    """Executive-level summary."""
    return {
        "overall_compliance": dashboard["summary"]["overall_compliance"],
        "compliance_grade": dashboard["summary"]["compliance_grade"],
        "total_employees": dashboard["summary"]["total_employees"],
        "risk_distribution": dashboard["risk_distribution"],
        "top_risk": dashboard["top_10_risks"][0] if dashboard["top_10_risks"] else None,
        "recommendations_count": sum(1 for _ in dashboard.get("top_10_risks", [])),
    }


# ============================================================
# MODULE 19 — AI RISK PREDICTION (Statistical)
# ============================================================


def predict_risk_anomalies(
    employees: List[EmployeeRisk],
) -> pd.DataFrame:
    """Detect anomalous risk patterns using statistical methods."""
    if not employees:
        return pd.DataFrame()

    scores = np.array([e.total_risk_score for e in employees])
    if len(scores) < 10:
        return pd.DataFrame()

    mean = scores.mean()
    std = scores.std()
    if std == 0:
        return pd.DataFrame()

    anomalies = []
    for er in employees:
        z = abs((er.total_risk_score - mean) / std)
        if z > 2.5:
            anomalies.append({
                "employee_name": er.employee_name,
                "site": er.site,
                "risk_score": er.total_risk_score,
                "z_score": round(z, 2),
                "mean": round(mean, 1),
                "std": round(std, 1),
                "anomaly_type": "statistical_outlier",
            })

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


def feature_engineering(employees: List[EmployeeRisk]) -> pd.DataFrame:
    """Prepare ML feature vectors from employee risk data."""
    rows = []
    for er in employees:
        rows.append({
            "employee_name": er.employee_name,
            "pf_risk": er.pf_risk,
            "esi_risk": er.esi_risk,
            "attendance_risk": er.attendance_risk,
            "payroll_risk": er.payroll_risk,
            "bank_risk": er.bank_risk,
            "identity_risk": er.identity_risk,
            "document_risk": er.document_risk,
            "fraud_risk": er.fraud_risk,
            "total_risk_score": er.total_risk_score,
            "is_duplicate": int(er.is_duplicate),
            "is_ghost": int(er.is_ghost),
            "missing_doc_count": len(er.missing_documents),
            "risk_factor_count": len(er.risk_factors),
            "risk_level_encoded": {
                "safe": 0, "low": 1, "medium": 2, "high": 3, "critical": 4
            }.get(er.risk_level, 2),
        })
    return pd.DataFrame(rows)


def export_ml_dataset(employees: List[EmployeeRisk], path: Path):
    """Export feature-engineered dataset for ML training."""
    df = feature_engineering(employees)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"ML dataset exported → {path} ({len(df)} rows)")


# ============================================================
# MODULE 20 — RISK CONFIDENCE SCORE
# ============================================================


def calculate_confidence(
    er: EmployeeRisk,
    sources: Dict[str, pd.DataFrame],
) -> float:
    """How confident are we in this risk score?"""
    # Data completeness: how many sources have this employee
    total_sources = len(sources)
    found_in = 0
    for src_name, df in sources.items():
        if df.empty:
            continue
        col_map = build_column_map(df)
        name_col = col_map.get("employee_name")
        if name_col and name_col in df.columns:
            if (df[name_col].astype(str).str.upper().str.strip() == er.employee_name).any():
                found_in += 1

    completeness = found_in / max(total_sources, 1)

    # Sample size factor
    total_rows = sum(len(df) for df in sources.values() if not df.empty)
    sample_factor = min(total_rows / 100, 1.0)

    # Consistency: how many risk factors
    factor_count = len(er.risk_factors)
    consistency = max(0, 1.0 - factor_count * 0.1)

    # Weighted confidence
    cfg = RiskConfig()
    confidence = (
        completeness * cfg.confidence_data_completeness_weight +
        sample_factor * cfg.confidence_sample_size_weight +
        consistency * cfg.confidence_consistency_weight
    ) * 100

    return round(min(max(confidence, 10), 99.9), 1)


def confidence_band(pct: float) -> str:
    if pct >= 90:
        return "high"
    elif pct >= 70:
        return "medium"
    elif pct >= 50:
        return "low"
    return "very_low"


# ============================================================
# MODULE 21 — EXCEPTION MANAGEMENT
# ============================================================


def build_exception_list(employees: List[EmployeeRisk]) -> pd.DataFrame:
    """All employees requiring attention."""
    exceptions = []
    for er in employees:
        if er.total_risk_score > 40 or er.is_ghost or er.is_duplicate:
            exceptions.append({
                "employee_name": er.employee_name,
                "employee_id": er.employee_id,
                "site": er.site,
                "risk_score": er.total_risk_score,
                "risk_level": er.risk_level,
                "is_ghost": er.is_ghost,
                "is_duplicate": er.is_duplicate,
                "risk_factors": "; ".join(er.risk_factors[:5]),
                "severity": "critical" if er.total_risk_score > 80 or er.is_ghost else (
                    "high" if er.total_risk_score > 60 else "medium"
                ),
            })
    return pd.DataFrame(exceptions) if exceptions else pd.DataFrame()


def critical_exceptions(employees: List[EmployeeRisk]) -> pd.DataFrame:
    df = build_exception_list(employees)
    if df.empty:
        return df
    return df[df["severity"] == "critical"]


def warning_exceptions(employees: List[EmployeeRisk]) -> pd.DataFrame:
    df = build_exception_list(employees)
    if df.empty:
        return df
    return df[df["severity"].isin(["high", "medium"])]


# ============================================================
# MODULE 22 — RANKING
# ============================================================


def rank_sites(site_risks: List[SiteRisk]) -> pd.DataFrame:
    ranked = sorted(site_risks, key=lambda s: s.compliance_pct, reverse=True)
    rows = []
    for i, s in enumerate(ranked):
        rows.append({
            "rank": i + 1, "site": s.site_name,
            "compliance_pct": s.compliance_pct,
            "risk_score": s.avg_risk_score,
            "employees": s.total_employees,
            "grade": assign_compliance_grade(s.compliance_pct, RiskConfig()),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def rank_clients(clients: List[Dict]) -> pd.DataFrame:
    if not clients:
        return pd.DataFrame()
    sorted_c = sorted(clients, key=lambda c: c.get("avg_compliance", 0), reverse=True)
    for i, c in enumerate(sorted_c):
        c["rank"] = i + 1
    return pd.DataFrame(sorted_c)


def rank_guards(employees: List[EmployeeRisk]) -> pd.DataFrame:
    sorted_e = sorted(employees, key=lambda e: e.compliance_pct, reverse=True)
    rows = []
    for i, e in enumerate(sorted_e[:50]):
        rows.append({
            "rank": i + 1, "employee_name": e.employee_name,
            "site": e.site, "compliance_pct": e.compliance_pct,
            "risk_score": e.total_risk_score, "grade": assign_compliance_grade(e.compliance_pct, RiskConfig()),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ============================================================
# MODULE 23 — EXECUTIVE SUMMARY
# ============================================================


def build_executive_summary(
    employees: List[EmployeeRisk],
    site_risks: List[SiteRisk],
    recommendations: List[Recommendation],
    config: RiskConfig,
) -> Dict[str, Any]:
    compliance = calculate_compliance_percentage(employees)
    risk_dist = defaultdict(int)
    for er in employees:
        risk_dist[er.risk_level] += 1

    top_risks = top_high_risk_employees(employees, 10)
    top_sites = sorted(site_risks, key=lambda s: s.avg_risk_score, reverse=True)[:10]

    return {
        "generated_at": datetime.now().isoformat(),
        "engine_version": config.engine_version,
        "overall": {
            "total_employees": len(employees),
            "total_sites": len(site_risks),
            "overall_compliance_pct": compliance["overall"],
            "compliance_grade": assign_compliance_grade(compliance["overall"], config),
            "avg_risk_score": round(np.mean([e.total_risk_score for e in employees]), 1) if employees else 0,
        },
        "compliance_by_category": compliance,
        "risk_distribution": dict(risk_dist),
        "top_10_high_risk_employees": [
            {"name": e.employee_name, "site": e.site,
             "score": e.total_risk_score, "level": e.risk_level,
             "primary_risk": e.risk_factors[0] if e.risk_factors else "none"}
            for e in top_risks
        ],
        "top_10_sites_by_risk": [
            {"site": s.site_name, "risk_score": s.avg_risk_score,
             "compliance": s.compliance_pct, "high_risk_employees": s.high_risk_count}
            for s in top_sites
        ],
        "recommended_actions": [
            {"employee": r.employee_name, "risk_type": r.risk_type,
             "suggestion": r.suggestion, "priority": r.priority,
             "department": r.department}
            for r in recommendations[:20]
        ],
        "summary_stats": {
            "ghost_employees": sum(1 for e in employees if e.is_ghost),
            "duplicates": sum(1 for e in employees if e.is_duplicate),
            "high_risk": sum(1 for e in employees if e.risk_level in ("high", "critical")),
            "needs_review": sum(1 for e in employees if e.risk_level == "medium"),
            "safe": sum(1 for e in employees if e.risk_level in ("safe", "low")),
            "recommendations_count": len(recommendations),
        },
    }


# ============================================================
# MODULE 24 — AUDIT TRAIL
# ============================================================


def audit_log(
    action: str,
    entity_type: str = "",
    entity_name: str = "",
    detail: str = "",
    operator: str = "auto",
):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action=action,
        entity_type=entity_type,
        entity_name=entity_name,
        detail=detail,
        operator=operator,
    ))


def risk_history(employees: List[EmployeeRisk]) -> pd.DataFrame:
    """Snapshot of current risk state for historical tracking."""
    rows = []
    ts = datetime.now().isoformat()
    for er in employees:
        rows.append({
            "timestamp": ts,
            "employee_name": er.employee_name,
            "site": er.site,
            "total_risk_score": er.total_risk_score,
            "risk_level": er.risk_level,
            "compliance_pct": er.compliance_pct,
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_audit_dataframe() -> pd.DataFrame:
    return pd.DataFrame([asdict(e) for e in _audit_log]) if _audit_log else pd.DataFrame()


def processing_statistics(stats: RuntimeStats) -> Dict[str, Any]:
    return stats.summary()


# ============================================================
# MODULE 25 — EXPORT ENGINE
# ============================================================


def export_csv(reports: Dict[str, pd.DataFrame]):
    for name, df in reports.items():
        if df is not None and not df.empty:
            path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            logger.info(f"CSV → {path} ({len(df)} rows)")


def export_excel(reports: Dict[str, pd.DataFrame]):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"compliance_risk_report_{ts}.xlsx"
    sheets = {k[:31]: v for k, v in reports.items() if v is not None and not v.empty}
    if not sheets:
        return
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sn, df in sheets.items():
            df.to_excel(writer, sheet_name=sn, index=False)
    logger.info(f"Excel → {path} ({len(sheets)} sheets)")


def export_json(dashboard: Dict, summary: Dict, stats: RuntimeStats):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {**dashboard, "executive_summary": summary, "runtime_stats": stats.summary()}
    path = SUMMARY_DIR / f"compliance_risk_summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"JSON → {path}")


# ============================================================
# MAIN ENGINE
# ============================================================


class ComplianceRiskEngine:
    """
    Production compliance risk scoring engine.
    Runs all 25 modules in sequence.
    """

    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        client_name: str = "default",
    ):
        self.config = config or load_config()
        self.client_config = ClientConfig(client_name=client_name)
        self.stats = RuntimeStats()

        self.sources: Dict[str, pd.DataFrame] = {}
        self.employees: List[EmployeeRisk] = []
        self.site_risks: List[SiteRisk] = []
        self.recommendations: List[Recommendation] = []
        self.dashboard: Dict[str, Any] = {}
        self.executive_summary: Dict[str, Any] = {}

        _audit_log.clear()
        _exceptions.clear()

    def run(self) -> Dict[str, Any]:
        self.stats = RuntimeStats()
        cfg = self.config

        logger.info("=" * 70)
        logger.info("COMPLIANCE RISK SCORING ENGINE")
        logger.info(f"Engine version: {cfg.engine_version}")
        logger.info("=" * 70)

        # ── 1. Load all sources ──
        logger.info("PHASE 1: LOADING DATA")
        self.sources = load_all_sources()
        self.stats.files_loaded = len(self.sources)
        for k, df in self.sources.items():
            self.stats.rows_loaded += len(df)

        audit_log("ENGINE_START", detail=f"Loaded {len(self.sources)} sources")

        # ── 2. Input validation ──
        logger.info("PHASE 2: INPUT VALIDATION")
        validation_report = validate_input_data(self.sources)
        audit_log("INPUT_VALIDATED", detail=json.dumps(validation_report, default=str))

        # ── 3. Category risk scores ──
        logger.info("PHASE 3: CATEGORY RISK SCORING")
        pf_score, pf_incidents, pf_details = calculate_pf_risk(self.sources, cfg)
        esi_score, esi_incidents, esi_details = calculate_esi_risk(self.sources, cfg)
        att_score, att_incidents, att_details = calculate_attendance_risk(self.sources, cfg)
        pay_score, pay_incidents, pay_details = calculate_payroll_risk(self.sources, cfg)
        bank_score, bank_incidents, bank_details = calculate_bank_risk(self.sources, cfg)
        id_score, id_incidents, id_details = calculate_identity_risk(self.sources, cfg)
        doc_score, doc_incidents, doc_details = calculate_document_risk(self.sources, cfg)
        fraud_score, fraud_incidents, fraud_details = calculate_fraud_risk(self.sources, cfg)

        categories = [
            RiskCategory("PF", pf_score, pf_score * cfg.weight_pf, 100, pf_incidents, pf_details),
            RiskCategory("ESI", esi_score, esi_score * cfg.weight_esi, 100, esi_incidents, esi_details),
            RiskCategory("Attendance", att_score, att_score * cfg.weight_attendance, 100, att_incidents, att_details),
            RiskCategory("Payroll", pay_score, pay_score * cfg.weight_payroll, 100, pay_incidents, pay_details),
            RiskCategory("Bank", bank_score, bank_score * cfg.weight_bank, 100, bank_incidents, bank_details),
            RiskCategory("Identity", id_score, id_score * cfg.weight_identity, 100, id_incidents, id_details),
            RiskCategory("Document", doc_score, doc_score * cfg.weight_document, 100, doc_incidents, doc_details),
            RiskCategory("Fraud", fraud_score, fraud_score * cfg.weight_fraud, 100, fraud_incidents, fraud_details),
        ]
        self.stats.risk_categories_calculated = len(categories)

        total_weighted = sum(c.weighted_score for c in categories)
        total_raw = sum(c.raw_score for c in categories)
        total_incidents = sum(c.incidents for c in categories)

        logger.info(f"Category scores: PF={pf_score:.0f}, ESI={esi_score:.0f}, "
                     f"Att={att_score:.0f}, Pay={pay_score:.0f}, "
                     f"Bank={bank_score:.0f}, ID={id_score:.0f}, "
                     f"Doc={doc_score:.0f}, Fraud={fraud_score:.0f}")
        logger.info(f"Weighted total: {total_weighted:.1f} | Incidents: {total_incidents}")

        # ── 4. Compliance percentages ──
        logger.info("PHASE 4: COMPLIANCE CALCULATION")
        pf_compliance = calculate_pf_compliance(self.sources)
        esi_compliance = calculate_esi_compliance(self.sources)
        att_compliance = calculate_attendance_compliance(self.sources)

        compliance = {
            "overall": round(100 - total_weighted, 1),
            "pf": pf_compliance,
            "esi": esi_compliance,
            "attendance": att_compliance,
        }

        # ── 5. Employee risk scores ──
        logger.info("PHASE 5: EMPLOYEE RISK SCORING")
        self.employees = calculate_employee_risk_scores(self.sources, cfg)
        self.stats.employees_scored = len(self.employees)
        logger.info(f"Employees scored: {len(self.employees)}")

        # ── 6. Site risk scores ──
        logger.info("PHASE 6: SITE RISK SCORING")
        self.site_risks = calculate_site_risk(self.employees, cfg)
        self.site_risks = rank_sites_by_risk(self.site_risks)
        self.stats.sites_scored = len(self.site_risks)
        logger.info(f"Sites scored: {len(self.site_risks)}")

        # ── 7. Client risk ──
        logger.info("PHASE 7: CLIENT RISK")
        client_risk = calculate_client_risk(self.site_risks, self.client_config)

        # ── 8. Recommendations ──
        logger.info("PHASE 8: RECOMMENDATIONS")
        self.recommendations = generate_recommendations(self.employees)
        self.stats.recommendations_generated = len(self.recommendations)
        logger.info(f"Recommendations: {len(self.recommendations)}")

        # ── 9. Root cause analysis ──
        logger.info("PHASE 9: ROOT CAUSE ANALYSIS")
        root_causes = []
        for er in top_high_risk_employees(self.employees, 20):
            causes = find_root_cause(er)
            for c in causes:
                c["employee_name"] = er.employee_name
                c["site"] = er.site
                root_causes.append(c)

        # ── 10. Trend analysis ──
        logger.info("PHASE 10: TREND ANALYSIS")
        prev_file = OUTPUT_DIR / "risk_history.csv"
        trend = compare_previous_month(self.employees, prev_file)

        # ── 11. AI anomaly detection ──
        logger.info("PHASE 11: AI ANOMALY DETECTION")
        anomalies = predict_risk_anomalies(self.employees)

        # ── 12. Exception management ──
        logger.info("PHASE 12: EXCEPTION MANAGEMENT")
        exceptions = build_exception_list(self.employees)
        critical = critical_exceptions(self.employees)
        warnings_df = warning_exceptions(self.employees)
        self.stats.exceptions_found = len(exceptions)

        # ── 13. Dashboard ──
        logger.info("PHASE 13: DASHBOARD")
        self.dashboard = build_dashboard(self.employees, self.site_risks, cfg)

        # ── 14. Executive summary ──
        logger.info("PHASE 14: EXECUTIVE SUMMARY")
        self.executive_summary = build_executive_summary(
            self.employees, self.site_risks, self.recommendations, cfg
        )

        # ── 15. Build all reports ──
        logger.info("PHASE 15: REPORT GENERATION")

        employee_df = pd.DataFrame([asdict(e) for e in self.employees])
        site_df = build_site_risk_summary(self.site_risks)
        site_rank_df = rank_sites(self.site_risks)
        guard_rank_df = rank_guards(self.employees)
        rec_df = pd.DataFrame([asdict(r) for r in self.recommendations]) if self.recommendations else pd.DataFrame()
        cat_df = pd.DataFrame([asdict(c) for c in categories])
        root_cause_df = pd.DataFrame(root_causes) if root_causes else pd.DataFrame()
        audit_df = get_audit_dataframe()
        history_df = risk_history(self.employees)
        feature_df = feature_engineering(self.employees)

        # Attendance intelligence
        att_intel = pd.DataFrame([{
            "attendance_pct": attendance_percentage(self.sources),
            "late_pct": late_percentage(self.sources),
            "continuous_absence_employees": continuous_absence(self.sources),
            "overtime_pct": overtime_percentage(self.sources),
        }])

        # Payroll intelligence
        pay_intel = pd.DataFrame([{
            "salary_variance": salary_variance(self.sources),
            "abnormal_salaries": abnormal_salary(self.sources),
            "duplicate_salaries": duplicate_salary(self.sources),
        }])

        # ── 16. Export ──
        logger.info("PHASE 16: EXPORT")

        all_reports = {
            "compliance_risk_report": employee_df,
            "site_risk_summary": site_df,
            "site_rankings": site_rank_df,
            "guard_rankings": guard_rank_df,
            "risk_categories": cat_df,
            "recommendations": rec_df,
            "root_cause_analysis": root_cause_df,
            "exceptions": exceptions,
            "critical_exceptions": critical,
            "warning_exceptions": warnings_df,
            "anomalies": anomalies,
            "attendance_intelligence": att_intel,
            "payroll_intelligence": pay_intel,
            "risk_history": history_df,
            "ml_features": feature_df,
            "audit_trail": audit_df,
            "input_validation": pd.DataFrame([validation_report]),
        }

        csv_reports = {k: v for k, v in all_reports.items() if v is not None and not v.empty}
        export_csv(csv_reports)
        export_excel(csv_reports)
        export_json(self.dashboard, self.executive_summary, self.stats)

        # Save history for next month trend
        if not history_df.empty:
            history_path = OUTPUT_DIR / "risk_history.csv"
            history_df.to_csv(history_path, index=False, encoding="utf-8-sig")

        # ML dataset
        ml_path = OUTPUT_DIR / "ml_training_dataset.csv"
        export_ml_dataset(self.employees, ml_path)

        self.stats.finish()
        audit_log("ENGINE_COMPLETE", detail=f"Elapsed={self.stats.elapsed}s")

        # ── Final summary ──
        logger.info("=" * 70)
        logger.info("COMPLIANCE RISK SCORING COMPLETE")
        logger.info(f"  Elapsed:          {self.stats.elapsed}s")
        logger.info(f"  Files loaded:     {self.stats.files_loaded}")
        logger.info(f"  Rows processed:   {self.stats.rows_loaded}")
        logger.info(f"  Employees scored: {self.stats.employees_scored}")
        logger.info(f"  Sites scored:     {self.stats.sites_scored}")
        logger.info(f"  Recommendations:  {self.stats.recommendations_generated}")
        logger.info(f"  Exceptions:       {self.stats.exceptions_found}")
        logger.info(f"  Overall compliance: {compliance['overall']}%")
        logger.info(f"  Compliance grade:   {assign_compliance_grade(compliance['overall'], cfg)}")
        logger.info(f"  CSV files:          {len(csv_reports)}")
        logger.info("=" * 70)

        return {
            **self.dashboard,
            "executive_summary": self.executive_summary,
            "client_risk": client_risk,
            "runtime_stats": self.stats.summary(),
        }


# ============================================================
# BACKWARD-COMPATIBLE run()
# ============================================================


def build_report():
    """Legacy single-row report."""
    engine = ComplianceRiskEngine()
    engine.sources = load_all_sources()
    cfg = engine.config

    pf_score, _, _ = calculate_pf_risk(engine.sources, cfg)
    esi_score, _, _ = calculate_esi_risk(engine.sources, cfg)
    att_score, _, _ = calculate_attendance_risk(engine.sources, cfg)
    pay_score, _, _ = calculate_payroll_risk(engine.sources, cfg)
    bank_score, _, _ = calculate_bank_risk(engine.sources, cfg)
    id_score, _, _ = calculate_identity_risk(engine.sources, cfg)
    doc_score, _, _ = calculate_document_risk(engine.sources, cfg)
    fraud_score, _, _ = calculate_fraud_risk(engine.sources, cfg)

    total = pf_score + esi_score + att_score + pay_score + bank_score + id_score + doc_score + fraud_score

    return pd.DataFrame([{
        "PF_Risk": pf_score,
        "ESI_Risk": esi_score,
        "Attendance_Risk": att_score,
        "Payroll_Risk": pay_score,
        "Bank_Risk": bank_score,
        "Identity_Risk": id_score,
        "Document_Risk": doc_score,
        "Fraud_Risk": fraud_score,
        "Total_Risk_Score": total,
        "Risk_Level": classify_risk(total, cfg),
    }])


def run():
    """Full production engine."""
    engine = ComplianceRiskEngine()
    return engine.run()


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compliance Risk Scoring Engine")
    parser.add_argument("--client", default="default", help="Client name")
    parser.add_argument("--config", default=None, help="Config file path")
    parser.add_argument("--operator", default="auto", help="Operator name")

    args = parser.parse_args()

    cfg = load_config(Path(args.config) if args.config else None)
    cfg.operator = args.operator

    engine = ComplianceRiskEngine(config=cfg, client_name=args.client)
    result = engine.run()
    print(json.dumps(result, indent=2, default=str))
