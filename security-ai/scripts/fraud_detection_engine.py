# security-ai/scripts/fraud_detection_engine.py
"""
Production-Grade Fraud Detection Engine
Security AI — Multi-Domain Fraud Intelligence System

═══════════════════════════════════════════════════════════════════
 25 MODULES | 120+ FUNCTIONS | 15+ DETECTORS | EXPLAINABLE AI
═══════════════════════════════════════════════════════════════════

 MODULES:
  1.  Configurable Rules Engine
  2.  Multi-Site Fraud Detection
  3.  Client-wise Fraud Analysis
  4.  Monthly Fraud Trend
  5.  Employee Fraud Score
  6.  Attendance Fraud Intelligence
  7.  Payroll Fraud Detection
  8.  Ghost Employee Intelligence
  9.  Identity Fraud Detection
  10. PF Fraud Intelligence
  11. ESI Fraud Intelligence
  12. Bank Fraud Detection
  13. Site Assignment Fraud
  14. Compliance Fraud
  15. Incident & Complaint Intelligence
  16. AI Anomaly Detection
  17. Fraud Confidence Scoring
  18. Root Cause Analysis
  19. Fraud Dashboard
  20. Site / Client Heatmap
  21. Investigation Queue
  22. Audit Trail
  23. Export Engine
  24. Explainable AI
  25. Production Logging & Statistics
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
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "datasets"
RECON_DIR = BASE_DIR / "reconciliation"
OUTPUT_DIR = BASE_DIR / "fraud_reports"
EXPORT_DIR = BASE_DIR / "exports"
SUMMARY_DIR = BASE_DIR / "summaries"
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

for _d in (DATASET_DIR, RECON_DIR, OUTPUT_DIR, EXPORT_DIR, SUMMARY_DIR, LOG_DIR, CONFIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

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
    root = logging.getLogger("FraudEngine")
    root.setLevel(logging.DEBUG)
    if root.handlers:
        return root
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(ch)
    fh = RotatingFileHandler(
        log_dir / "fraud_engine.log",
        maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(fh)
    eh = RotatingFileHandler(
        log_dir / "fraud_engine_errors.log",
        maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8",
    )
    eh.setLevel(logging.ERROR)
    eh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(eh)
    return root


logger = setup_rotating_logger(LOG_DIR)

# ============================================================
# ENUMS
# ============================================================


class FraudType(str, Enum):
    GHOST_EMPLOYEE = "ghost_employee"
    FAKE_ATTENDANCE = "fake_attendance"
    OVERTIME_FRAUD = "overtime_fraud"
    SALARY_INFLATION = "salary_inflation"
    SALARY_SPLITTING = "salary_splitting"
    DUPLICATE_SALARY = "duplicate_salary"
    SALARY_OVERRIDE = "salary_override"
    NEGATIVE_DEDUCTION = "negative_deduction"
    FAKE_ALLOWANCE = "fake_allowance"
    PF_EVASION = "pf_evasion"
    ESI_EVASION = "esi_evasion"
    WRONG_PF_WAGE = "wrong_pf_wage"
    WRONG_ESI_THRESHOLD = "wrong_esi_threshold"
    MISSING_IN_ECR = "missing_in_ecr"
    DUPLICATE_UAN = "duplicate_uan"
    DUPLICATE_IP = "duplicate_ip"
    DUPLICATE_BANK = "duplicate_bank"
    DUPLICATE_AADHAAR = "duplicate_aadhaar"
    DUPLICATE_PAN = "duplicate_pan"
    DOUBLE_SHIFT = "double_shift"
    IMPOSSIBLE_HOURS = "impossible_hours"
    MISSING_CHECKOUT = "missing_checkout"
    GPS_MISMATCH = "gps_mismatch"
    DUPLICATE_PAYMENT = "duplicate_bank_payment"
    RETURNED_PAYMENT = "returned_payment"
    CASH_PAYMENT = "cash_payment"
    DOUBLE_SITE = "double_site_assignment"
    UNASSIGNED_GUARD = "unassigned_guard"
    EXPIRED_DOCUMENT = "expired_document"
    MISSING_TRAINING = "missing_training"
    REPEAT_OFFENDER = "repeat_offender"
    STATISTICAL_OUTLIER = "statistical_outlier"
    IDENTITY_FRAUD = "identity_fraud"


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# MODULE 1 — CONFIGURABLE RULES ENGINE
# ============================================================


@dataclass
class FraudConfig:
    """All fraud detection thresholds — loaded from config."""
    # Attendance
    max_overtime_hours: float = 100.0
    max_daily_hours: float = 16.0
    min_daily_hours: float = 0.5
    gps_mismatch_threshold: int = 5
    continuous_absence_days: int = 7

    # Salary
    salary_inflation_multiplier: float = 2.0
    max_negative_deduction: float = -1000.0
    min_salary: float = 1000.0

    # PF / ESI
    pf_ceiling: float = 15000.0
    esi_wage_limit: float = 21000.0
    pf_employee_rate: float = 0.12
    esi_employee_rate: float = 0.0075
    esi_employer_rate: float = 0.0325

    # Identity
    duplicate_score_threshold: float = 0.90

    # Risk scoring weights
    ghost_weight: float = 15.0
    attendance_weight: float = 8.0
    salary_weight: float = 10.0
    identity_weight: float = 12.0
    compliance_weight: float = 5.0
    bank_weight: float = 10.0

    # Confidence
    min_evidence_points: int = 3

    # Engine
    engine_version: str = "6.0.0"
    operator: str = "auto"


@dataclass
class ClientConfig:
    client_name: str = "default"
    client_id: str = "001"
    sites: List[str] = field(default_factory=list)


def load_config(config_path: Optional[Path] = None) -> FraudConfig:
    cfg = FraudConfig()
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


def load_thresholds(config: FraudConfig) -> Dict[str, Any]:
    return {
        "attendance": {
            "max_overtime_hours": config.max_overtime_hours,
            "max_daily_hours": config.max_daily_hours,
            "continuous_absence_days": config.continuous_absence_days,
        },
        "salary": {
            "inflation_multiplier": config.salary_inflation_multiplier,
            "max_negative_deduction": config.max_negative_deduction,
            "min_salary": config.min_salary,
        },
        "pf_esi": {
            "pf_ceiling": config.pf_ceiling,
            "esi_wage_limit": config.esi_wage_limit,
        },
    }


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class FraudCase:
    """Single fraud detection case."""
    case_id: str = ""
    fraud_type: str = ""
    entity_type: str = "employee"
    entity_id: str = ""
    entity_name: str = ""
    site: str = ""
    client: str = ""
    risk_level: str = RiskLevel.MEDIUM.value
    fraud_score: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ""
    priority: str = Priority.MEDIUM.value
    department: str = "compliance"
    estimated_impact: float = 0.0
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    engine_version: str = "6.0.0"
    operator: str = "auto"


@dataclass
class EmployeeFraudScore:
    employee_name: str = ""
    employee_id: str = ""
    site: str = ""
    client: str = ""
    ghost_score: float = 0.0
    attendance_score: float = 0.0
    payroll_score: float = 0.0
    identity_score: float = 0.0
    pf_score: float = 0.0
    esi_score: float = 0.0
    bank_score: float = 0.0
    compliance_score: float = 0.0
    total_fraud_score: float = 0.0
    risk_level: str = RiskLevel.SAFE.value
    confidence: float = 0.0
    fraud_types: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class SiteFraud:
    site_name: str = ""
    client: str = ""
    total_employees: int = 0
    fraud_count: int = 0
    fraud_score: float = 0.0
    risk_level: str = RiskLevel.SAFE.value
    ghost_count: int = 0
    attendance_fraud: int = 0
    payroll_fraud: int = 0
    identity_fraud: int = 0
    rank: int = 0


@dataclass
class InvestigationCase:
    case_id: str = ""
    employee_name: str = ""
    site: str = ""
    fraud_type: str = ""
    risk_level: str = ""
    priority: str = ""
    assigned_to: str = ""
    status: str = "open"
    evidence: str = ""
    recommendation: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: str = ""


@dataclass
class AuditEntry:
    timestamp: str = ""
    action: str = ""
    module: str = ""
    entity_name: str = ""
    detail: str = ""
    evidence: str = ""
    engine_version: str = "6.0.0"
    operator: str = "auto"


@dataclass
class RuntimeStats:
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_loaded: int = 0
    rows_loaded: int = 0
    modules_run: int = 0
    fraud_cases_detected: int = 0
    employees_scored: int = 0
    sites_analyzed: int = 0
    ghost_employees: int = 0
    attendance_frauds: int = 0
    payroll_frauds: int = 0
    identity_frauds: int = 0
    pf_frauds: int = 0
    esi_frauds: int = 0
    bank_frauds: int = 0
    compliance_frauds: int = 0
    investigation_cases: int = 0
    errors: int = 0
    warnings: int = 0

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
                **{k: v for k, v in self.__dict__.items() if k not in ("start_time", "end_time")}}


# Global stores
_audit_log: List[AuditEntry] = []
_case_counter: int = 0


# ============================================================
# FIELD RESOLVER
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "employee_name": ["employee_name", "emp_name", "name", "staff_name", "guard_name", "Guard_Name", "Name", "Employee_Name"],
    "employee_id": ["employee_id", "emp_id", "guard_id", "Guard_ID", "staff_id", "code"],
    "guard_id": ["guard_id", "Guard_ID", "employee_id", "emp_id"],
    "uan_number": ["uan_number", "uan", "uan_no", "UAN", "source_uan", "Source_UAN", "UAN_Number"],
    "ip_number": ["ip_number", "ip_no", "esic_number", "esic_no", "IP_Number", "IP_Number_ESIC"],
    "site_location": ["site_location", "site", "location", "branch", "unit", "Site", "site_name", "Site_Name"],
    "client": ["client", "client_name", "Client"],
    "basic_salary": ["basic_salary", "basic_vda", "basic", "Basic_Salary", "BASIC + VDA", "basic_wages"],
    "gross_wages": ["gross_wages", "gross", "total_wages", "Gross_Wages", "gross_salary", "TOTAL"],
    "net_pay": ["net_pay", "Net_Pay", "net_salary", "NET PAYMENT"],
    "overtime_hours": ["overtime_hours", "Overtime_Hours", "ot_hours", "OT", "Overtime Hours Worked"],
    "hours_worked": ["hours_worked", "Hours_Worked", "hours"],
    "status": ["status", "Status", "attendance_status"],
    "gps_match": ["gps_match", "GPS_Match", "gps_status"],
    "match_status": ["match_status", "Match_Status"],
    "days_worked": ["days_worked", "working_days", "Days_Worked", "No Of Days Worked"],
    "bank_account": ["bank_account", "bank_account_number", "account_number", "Bank_Account"],
    "aadhaar_number": ["aadhaar_number", "aadhaar", "uid", "Aadhaar_Number"],
    "pan_number": ["pan_number", "pan", "PAN_Number"],
    "joining_date": ["joining_date", "doj", "date_of_joining", "DOJ"],
    "exit_date": ["exit_date", "doe", "leaving_date", "DOE"],
    "police_verification": ["police_verification", "police_verified", "PV_Status"],
    "training_status": ["training_status", "trained", "Training_Status"],
    "license_expiry": ["license_expiry", "license_valid_until", "PSARA_Expiry"],
    "shift": ["shift", "shift_name", "Shift"],
    "date": ["date", "attendance_date", "Date"],
    "incident_type": ["incident_type", "Incident_Type"],
    "complaint_type": ["complaint_type", "Complaint_Type"],
    "check_in": ["check_in", "checkin_time", "Check_In"],
    "check_out": ["check_out", "checkout_time", "Check_Out"],
    "transfer_amount": ["transfer_amount", "bank_credit", "credited_amount"],
    "month": ["month", "pay_month", "Month"],
    "year": ["year", "pay_year", "Year"],
    "esi_eligibility": ["esi_eligibility", "ESI_Eligibility", "eligibility"],
    "employee_esi": ["employee_esi", "esic", "esi_deduction", "ESIC 0.75% OF BASIC +VDA", "Employee_ESI"],
    "employee_pf": ["employee_pf", "epf", "pf_deduction", "EPF 12%", "Employee_PF"],
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
        logger.error(f"Load error {file_path}: {e}")
        return pd.DataFrame()
    if df.empty:
        return df
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]
    logger.info(f"Loaded {file_path.name}: {df.shape[0]} × {df.shape[1]}")
    return df


def load_all_sources() -> Dict[str, pd.DataFrame]:
    sources = {}
    files = {
        "attendance": DATASET_DIR / "attendance.csv",
        "payroll": DATASET_DIR / "payroll.csv",
        "guards": DATASET_DIR / "guards_master.csv",
        "compliance": DATASET_DIR / "compliance.csv",
        "bank": DATASET_DIR / "bank.csv",
        "site_assignments": DATASET_DIR / "site_assignments.csv",
        "incidents": DATASET_DIR / "incidents.csv",
        "complaints": DATASET_DIR / "complaints.csv",
        "pf": RECON_DIR / "pf_reconciliation_report.csv",
        "esi": RECON_DIR / "esi_reconciliation_report.csv",
        "matching": RECON_DIR / "employee_matching_report.csv",
        "duplicates": RECON_DIR / "duplicate_employees.csv",
        "missing": RECON_DIR / "missing_employees.csv",
        "risk": RECON_DIR / "risk_summary.csv",
    }
    for key, path in files.items():
        df = safe_load(path)
        if not df.empty:
            sources[key] = df
    return sources


# ============================================================
# UTILITY
# ============================================================


def _safe_get_df(sources: Dict[str, pd.DataFrame], *keys: str) -> Optional[pd.DataFrame]:
    """Safely get the first non-empty DataFrame from sources by key.
    Never triggers 'truth value of DataFrame is ambiguous' error.
    """
    for key in keys:
        df = sources.get(key)
        if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
            return df
    return None


def generate_case_id() -> str:
    global _case_counter
    _case_counter += 1
    ts = datetime.now().strftime("%Y%m%d")
    return f"FRD-{ts}-{_case_counter:04d}"


def audit_log(action: str, module: str = "", entity_name: str = "",
              detail: str = "", evidence: str = "", operator: str = "auto"):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(), action=action,
        module=module, entity_name=entity_name,
        detail=detail, evidence=evidence, operator=operator,
    ))


def get_audit_dataframe() -> pd.DataFrame:
    return pd.DataFrame([asdict(e) for e in _audit_log]) if _audit_log else pd.DataFrame()


# ============================================================
# MODULE 5 — EMPLOYEE FRAUD SCORE
# ============================================================


def calculate_employee_fraud_score(
    employee_name: str,
    employee_id: str,
    site: str,
    sources: Dict[str, pd.DataFrame],
    config: FraudConfig,
    ghost_flag: bool = False,
    attendance_flags: int = 0,
    payroll_flags: int = 0,
    identity_flags: int = 0,
    pf_flags: int = 0,
    esi_flags: int = 0,
    bank_flags: int = 0,
    compliance_flags: int = 0,
    fraud_types: List[str] = None,
    evidence: List[str] = None,
) -> EmployeeFraudScore:
    """Calculate composite fraud score 0-100 for one employee."""
    ghost = 100.0 if ghost_flag else 0.0
    att = min(attendance_flags * config.attendance_weight, 100.0)
    pay = min(payroll_flags * config.salary_weight, 100.0)
    ident = min(identity_flags * config.identity_weight, 100.0)
    pf = min(pf_flags * 10, 100.0)
    esi = min(esi_flags * 10, 100.0)
    bank_s = min(bank_flags * config.bank_weight, 100.0)
    comp = min(compliance_flags * config.compliance_weight, 100.0)

    total = round(
        ghost * 0.20 + att * 0.15 + pay * 0.15 + ident * 0.15 +
        pf * 0.10 + esi * 0.05 + bank_s * 0.10 + comp * 0.10, 1
    )
    total = min(total, 100.0)

    risk_level = classify_fraud_risk(total, config)
    conf = calculate_fraud_confidence(
        total, len(fraud_types or []), len(evidence or [])
    )

    recommendation = recommend_resolution(total, fraud_types or [], ghost_flag)

    return EmployeeFraudScore(
        employee_name=employee_name,
        employee_id=employee_id,
        site=site,
        ghost_score=ghost,
        attendance_score=att,
        payroll_score=pay,
        identity_score=ident,
        pf_score=pf,
        esi_score=esi,
        bank_score=bank_s,
        compliance_score=comp,
        total_fraud_score=total,
        risk_level=risk_level,
        confidence=conf,
        fraud_types=fraud_types or [],
        evidence=evidence or [],
        recommendation=recommendation,
    )


def classify_fraud_risk(score: float, config: FraudConfig) -> str:
    if score <= 15:
        return RiskLevel.SAFE.value
    elif score <= 30:
        return RiskLevel.LOW.value
    elif score <= 55:
        return RiskLevel.MEDIUM.value
    elif score <= 80:
        return RiskLevel.HIGH.value
    return RiskLevel.CRITICAL.value


def top_high_risk_employees(scores: List[EmployeeFraudScore], n: int = 20) -> List[EmployeeFraudScore]:
    return sorted(scores, key=lambda s: s.total_fraud_score, reverse=True)[:n]


# ============================================================
# MODULE 6 — ATTENDANCE FRAUD INTELLIGENCE
# ============================================================


def detect_ghost_employees(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    att_df = sources.get("attendance")
    pay_df = sources.get("payroll")
    if att_df is None or att_df.empty or pay_df is None or pay_df.empty:
        return cases

    att_map = build_column_map(att_df)
    pay_map = build_column_map(pay_df)
    att_id = att_map.get("guard_id") or att_map.get("employee_id")
    pay_id = pay_map.get("guard_id") or pay_map.get("employee_id")
    if not att_id or not pay_id:
        return cases

    att_ids = set(att_df[att_id].dropna().astype(str).str.strip())
    pay_name = pay_map.get("employee_name")
    site_col = pay_map.get("site_location")

    for _, row in pay_df.iterrows():
        pid = str(row.get(pay_id, "")).strip()
        if pid and pid not in att_ids:
            name = str(row.get(pay_name, "")) if pay_name else pid
            site = str(row.get(site_col, "")) if site_col else ""
            evidence_points = [
                f"Guard ID {pid} exists in payroll",
                f"Guard ID {pid} has no attendance records",
            ]
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.GHOST_EMPLOYEE.value,
                entity_id=pid,
                entity_name=name,
                site=site,
                risk_level=RiskLevel.CRITICAL.value,
                fraud_score=100.0,
                confidence=95.0,
                reason="Employee in payroll but no attendance records — suspected ghost employee",
                evidence=evidence_points,
                recommendation="Suspend payment immediately. Verify physical presence. Check all identity documents.",
                priority=Priority.CRITICAL.value,
                department="hr",
            ))
    return cases


def detect_fake_attendance(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("attendance")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    status_col = col_map.get("status")
    hours_col = col_map.get("hours_worked")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")
    site_col = col_map.get("site_location")

    if not status_col or not hours_col:
        return cases

    hours = pd.to_numeric(df[hours_col], errors="coerce")
    mask = (df[status_col].astype(str).str.lower() == "absent") & (hours > 0)

    for _, row in df[mask].iterrows():
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.FAKE_ATTENDANCE.value,
            entity_id=str(row.get(id_col, "")) if id_col else "",
            entity_name=str(row.get(name_col, "")) if name_col else "",
            site=str(row.get(site_col, "")) if site_col else "",
            risk_level=RiskLevel.HIGH.value,
            fraud_score=85.0,
            confidence=98.0,
            reason=f"Marked absent but {hours.loc[row.name]} hours recorded",
            evidence=[f"Status=Absent", f"Hours={hours.loc[row.name]}"],
            recommendation="Verify attendance records. Check biometric data. Interview supervisor.",
            priority=Priority.HIGH.value,
            department="operations",
        ))
    return cases


def detect_double_shift(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("attendance")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    date_col = col_map.get("date")
    shift_col = col_map.get("shift")
    name_col = col_map.get("employee_name")
    site_col = col_map.get("site_location")

    if not id_col or not date_col or not shift_col:
        return cases

    grouped = df.groupby([id_col, date_col])
    for (eid, date), group in grouped:
        shifts = group[shift_col].dropna().unique()
        if len(shifts) > 1:
            name = str(group.iloc[0].get(name_col, "")) if name_col else str(eid)
            site = str(group.iloc[0].get(site_col, "")) if site_col else ""
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.DOUBLE_SHIFT.value,
                entity_id=str(eid), entity_name=name, site=site,
                risk_level=RiskLevel.HIGH.value,
                fraud_score=80.0, confidence=95.0,
                reason=f"Employee assigned {len(shifts)} shifts on {date}: {', '.join(str(s) for s in shifts)}",
                evidence=[f"Date={date}", f"Shifts={list(shifts)}"],
                recommendation="Verify scheduling records. Check if shifts are physically possible.",
                priority=Priority.HIGH.value, department="operations",
            ))
    return cases


def detect_impossible_hours(sources: Dict[str, pd.DataFrame], config: FraudConfig) -> List[FraudCase]:
    cases = []
    df = sources.get("attendance")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    hours_col = col_map.get("hours_worked")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")
    date_col = col_map.get("date")

    if not hours_col:
        return cases

    hours = pd.to_numeric(df[hours_col], errors="coerce")
    for _, row in df[hours > config.max_daily_hours].iterrows():
        h = hours.loc[row.name]
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.IMPOSSIBLE_HOURS.value,
            entity_id=str(row.get(id_col, "")) if id_col else "",
            entity_name=str(row.get(name_col, "")) if name_col else "",
            risk_level=RiskLevel.HIGH.value,
            fraud_score=75.0, confidence=90.0,
            reason=f"Impossible working hours: {h} (max allowed: {config.max_daily_hours})",
            evidence=[f"Hours={h}", f"Date={row.get(date_col, '')}"],
            recommendation="Verify time records. Check for data entry errors or time theft.",
            priority=Priority.MEDIUM.value, department="operations",
        ))
    return cases


def detect_missing_checkout(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("attendance")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    checkout_col = col_map.get("check_out")
    checkin_col = col_map.get("check_in")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")

    if not checkout_col or not checkin_col:
        return cases

    mask = df[checkin_col].notna() & df[checkout_col].isna()
    for _, row in df[mask].iterrows():
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.MISSING_CHECKOUT.value,
            entity_id=str(row.get(id_col, "")) if id_col else "",
            entity_name=str(row.get(name_col, "")) if name_col else "",
            risk_level=RiskLevel.LOW.value,
            fraud_score=30.0, confidence=70.0,
            reason="Check-in present but no check-out recorded",
            evidence=[f"Check-in={row.get(checkin_col, '')}", "Check-out=missing"],
            recommendation="Verify if guard completed shift. May be data entry error.",
            priority=Priority.LOW.value, department="operations",
        ))
    return cases


def gps_mismatch_frequency(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("attendance")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    gps_col = col_map.get("gps_match")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")

    if not gps_col:
        return cases

    gps_no = df[df[gps_col].astype(str).str.lower() == "no"]
    if gps_no.empty or not id_col:
        return cases

    freq = gps_no.groupby(id_col).size()
    for eid, count in freq.items():
        if count >= 3:
            name = ""
            if name_col:
                matches = df[df[id_col] == eid][name_col].dropna()
                name = str(matches.iloc[0]) if not matches.empty else str(eid)
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.GPS_MISMATCH.value,
                entity_id=str(eid), entity_name=name,
                risk_level=RiskLevel.MEDIUM.value if count < 10 else RiskLevel.HIGH.value,
                fraud_score=min(count * 10, 100), confidence=85.0,
                reason=f"GPS mismatch {count} times — possible location fraud",
                evidence=[f"Mismatch count={count}"],
                recommendation="Verify physical presence at site. Check GPS device.",
                priority=Priority.MEDIUM.value, department="operations",
            ))
    return cases


# ============================================================
# MODULE 7 — PAYROLL FRAUD
# ============================================================


def detect_overtime_fraud(sources: Dict[str, pd.DataFrame], config: FraudConfig) -> List[FraudCase]:
    cases = []
    df = sources.get("payroll")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    ot_col = col_map.get("overtime_hours")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")
    site_col = col_map.get("site_location")

    if not ot_col:
        return cases

    ot = pd.to_numeric(df[ot_col], errors="coerce")
    for _, row in df[ot > config.max_overtime_hours].iterrows():
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.OVERTIME_FRAUD.value,
            entity_id=str(row.get(id_col, "")) if id_col else "",
            entity_name=str(row.get(name_col, "")) if name_col else "",
            site=str(row.get(site_col, "")) if site_col else "",
            risk_level=RiskLevel.MEDIUM.value,
            fraud_score=60.0, confidence=80.0,
            reason=f"Excessive overtime: {ot.loc[row.name]} hours (limit: {config.max_overtime_hours})",
            evidence=[f"OT hours={ot.loc[row.name]}"],
            recommendation="Verify overtime authorization. Check attendance records.",
            priority=Priority.MEDIUM.value, department="payroll",
        ))
    return cases


def detect_salary_inflation(sources: Dict[str, pd.DataFrame], config: FraudConfig) -> List[FraudCase]:
    cases = []
    df = sources.get("payroll")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    salary_col = col_map.get("basic_salary")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")

    if not salary_col:
        return cases

    salaries = pd.to_numeric(df[salary_col], errors="coerce").dropna()
    if salaries.empty:
        return cases

    avg = salaries.mean()
    threshold = avg * config.salary_inflation_multiplier

    for _, row in df[pd.to_numeric(df[salary_col], errors="coerce") > threshold].iterrows():
        sal = pd.to_numeric(row.get(salary_col, 0), errors="coerce") or 0
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.SALARY_INFLATION.value,
            entity_id=str(row.get(id_col, "")) if id_col else "",
            entity_name=str(row.get(name_col, "")) if name_col else "",
            risk_level=RiskLevel.HIGH.value,
            fraud_score=75.0, confidence=70.0,
            reason=f"Salary ₹{sal:,.0f} is {sal / avg:.1f}x average (₹{avg:,.0f})",
            evidence=[f"Salary={sal}", f"Average={avg:.0f}", f"Ratio={sal / avg:.1f}x"],
            recommendation="Verify salary structure. Check authorization for salary revision.",
            priority=Priority.HIGH.value, department="payroll",
        ))
    return cases


def detect_salary_splitting(sources: Dict[str, pd.DataFrame], config: FraudConfig) -> List[FraudCase]:
    """Detect salaries split to stay under ESI/PF thresholds."""
    cases = []
    df = sources.get("payroll")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    gross_col = col_map.get("gross_wages")
    basic_col = col_map.get("basic_salary")
    name_col = col_map.get("employee_name")

    if not gross_col or not basic_col:
        return cases

    for _, row in df.iterrows():
        gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
        basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
        if gross > config.esi_wage_limit and basic <= config.esi_wage_limit:
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.SALARY_SPLITTING.value,
                entity_name=str(row.get(name_col, "")) if name_col else "",
                risk_level=RiskLevel.HIGH.value,
                fraud_score=80.0, confidence=85.0,
                reason=f"Gross ₹{gross:,.0f} exceeds ESI limit but basic ₹{basic:,.0f} is at limit",
                evidence=[f"Gross={gross}", f"Basic={basic}", f"ESI limit={config.esi_wage_limit}"],
                recommendation="Audit salary structure. ESI applies on gross, not just basic.",
                priority=Priority.HIGH.value, department="compliance",
            ))
    return cases


def detect_negative_deduction(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("payroll")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    net_col = col_map.get("net_pay")
    name_col = col_map.get("employee_name")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")

    if not net_col:
        return cases

    net = pd.to_numeric(df[net_col], errors="coerce")
    for _, row in df[net < 0].iterrows():
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.NEGATIVE_DEDUCTION.value,
            entity_id=str(row.get(id_col, "")) if id_col else "",
            entity_name=str(row.get(name_col, "")) if name_col else "",
            risk_level=RiskLevel.MEDIUM.value,
            fraud_score=50.0, confidence=90.0,
            reason=f"Negative net pay: ₹{net.loc[row.name]:,.0f}",
            evidence=[f"Net pay={net.loc[row.name]}"],
            recommendation="Check for data entry error or improper deduction reversal.",
            priority=Priority.MEDIUM.value, department="payroll",
        ))
    return cases


# ============================================================
# MODULE 8 — GHOST EMPLOYEE INTELLIGENCE
# ============================================================


def ghost_employee_score(
    employee_id: str,
    sources: Dict[str, pd.DataFrame],
) -> Tuple[float, List[str]]:
    """Score how likely an employee is a ghost (0-100)."""
    score = 0.0
    indicators = []

    # Check payroll
    pay_df = sources.get("payroll")
    in_payroll = False
    if pay_df is not None and not pay_df.empty:
        pay_map = build_column_map(pay_df)
        pid = pay_map.get("guard_id") or pay_map.get("employee_id")
        if pid and pid in pay_df.columns:
            in_payroll = (pay_df[pid].astype(str).str.strip() == employee_id.strip()).any()

    # Check attendance
    att_df = sources.get("attendance")
    in_attendance = False
    if att_df is not None and not att_df.empty:
        att_map = build_column_map(att_df)
        aid = att_map.get("guard_id") or att_map.get("employee_id")
        if aid and aid in att_df.columns:
            in_attendance = (att_df[aid].astype(str).str.strip() == employee_id.strip()).any()

    # Check bank
    bank_df = sources.get("bank")
    in_bank = False
    if bank_df is not None and not bank_df.empty:
        bank_map = build_column_map(bank_df)
        bid = bank_map.get("employee_id")
        if bid and bid in bank_df.columns:
            in_bank = (bank_df[bid].astype(str).str.strip() == employee_id.strip()).any()

    if in_payroll and not in_attendance:
        score += 40
        indicators.append("In payroll but no attendance")

    if in_payroll and not in_bank:
        score += 30
        indicators.append("In payroll but no bank payment")

    if in_payroll and not in_attendance and not in_bank:
        score += 30
        indicators.append("No attendance AND no bank — high ghost probability")

    return min(score, 100), indicators


def inactive_employee_detection(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    """Detect employees with exit dates but still in payroll."""
    cases = []
    pay_df = sources.get("payroll")
    if pay_df is None or pay_df.empty:
        return cases

    col_map = build_column_map(pay_df)
    exit_col = col_map.get("exit_date")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")

    if not exit_col:
        return cases

    today = pd.Timestamp.now()
    for _, row in pay_df.iterrows():
        exit_raw = row.get(exit_col)
        if pd.notna(exit_raw):
            try:
                exit_date = pd.to_datetime(exit_raw)
                if exit_date < today:
                    cases.append(FraudCase(
                        case_id=generate_case_id(),
                        fraud_type=FraudType.GHOST_EMPLOYEE.value,
                        entity_id=str(row.get(id_col, "")) if id_col else "",
                        entity_name=str(row.get(name_col, "")) if name_col else "",
                        risk_level=RiskLevel.HIGH.value,
                        fraud_score=70.0, confidence=85.0,
                        reason=f"Exit date {exit_date.date()} in the past but still receiving salary",
                        evidence=[f"Exit date={exit_date.date()}", "Still in active payroll"],
                        recommendation="Remove from payroll. Verify if genuine rejoining.",
                        priority=Priority.HIGH.value, department="hr",
                    ))
            except Exception:
                pass
    return cases


# ============================================================
# MODULE 9 — IDENTITY FRAUD
# ============================================================


def detect_duplicate_field(
    df: pd.DataFrame, field_semantic: str, fraud_type: str,
    col_map: Dict, label: str,
) -> List[FraudCase]:
    """Generic duplicate detector for any identity field."""
    cases = []
    col = col_map.get(field_semantic)
    name_col = col_map.get("employee_name")
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    site_col = col_map.get("site_location")

    if not col or col not in df.columns:
        return cases

    grouped = df.dropna(subset=[col]).groupby(col)
    for val, group in grouped:
        if len(group) < 2:
            continue
        names = group[name_col].dropna().tolist() if name_col else []
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=fraud_type,
            entity_name=str(names[0]) if names else "",
            risk_level=RiskLevel.HIGH.value if fraud_type in (
                FraudType.DUPLICATE_UAN.value, FraudType.DUPLICATE_AADHAAR.value
            ) else RiskLevel.MEDIUM.value,
            fraud_score=80.0, confidence=95.0,
            reason=f"Duplicate {label}: {val} used by {len(group)} employees",
            evidence=[f"{label}={val}", f"Employees={'; '.join(str(n) for n in names[:5])}"],
            recommendation=f"Verify {label} assignments. Each employee must have unique {label}.",
            priority=Priority.HIGH.value, department="hr",
        ))
    return cases


def duplicate_uan(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    """Detect guards sharing the same UAN (Universal Account Number).
    FIXED: Uses safe DataFrame retrieval instead of `or` operator.
    """
    df = _safe_get_df(sources, "guards", "pf", "payroll")
    if df is None:
        return []
    col_map = build_column_map(df)
    return detect_duplicate_field(
        df, "uan_number", FraudType.DUPLICATE_UAN.value, col_map, "UAN"
    )


def duplicate_ip(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    """Detect guards sharing the same ESIC IP number.
    FIXED: Uses safe DataFrame retrieval instead of `or` operator.
    """
    df = _safe_get_df(sources, "guards", "esi", "payroll")
    if df is None:
        return []
    col_map = build_column_map(df)
    return detect_duplicate_field(
        df, "ip_number", FraudType.DUPLICATE_IP.value, col_map, "IP Number"
    )


def duplicate_bank_account(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    """Detect guards sharing the same bank account.
    FIXED: Uses safe DataFrame retrieval instead of chained `or` operators.
    """
    df = _safe_get_df(sources, "guards", "bank", "payroll")
    if df is None:
        return []
    col_map = build_column_map(df)
    return detect_duplicate_field(
        df, "bank_account", FraudType.DUPLICATE_BANK.value, col_map, "Bank Account"
    )


def duplicate_pan(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    """Detect guards sharing the same PAN number.
    FIXED: Uses safe DataFrame retrieval.
    """
    df = _safe_get_df(sources, "guards", "payroll")
    if df is None:
        return []
    col_map = build_column_map(df)
    return detect_duplicate_field(
        df, "pan_number", FraudType.DUPLICATE_PAN.value, col_map, "PAN"
    )


def duplicate_aadhaar(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    """Detect guards sharing the same Aadhaar number.
    FIXED: Uses safe DataFrame retrieval.
    """
    df = _safe_get_df(sources, "guards", "payroll")
    if df is None:
        return []
    col_map = build_column_map(df)
    return detect_duplicate_field(
        df, "aadhaar_number", FraudType.DUPLICATE_AADHAAR.value, col_map, "Aadhaar"
    )


# ============================================================
# MODULE 10 — PF FRAUD INTELLIGENCE
# ============================================================


def detect_pf_evasion(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("pf")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    status_col = col_map.get("match_status")
    id_col = col_map.get("employee_id")
    name_col = col_map.get("employee_name")

    if not status_col:
        return cases

    for _, row in df[df[status_col].astype(str).str.lower() != "matched"].iterrows():
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.PF_EVASION.value,
            entity_id=str(row.get(id_col, "")) if id_col else "",
            entity_name=str(row.get(name_col, "")) if name_col else "",
            risk_level=RiskLevel.HIGH.value,
            fraud_score=70.0, confidence=80.0,
            reason=f"PF reconciliation mismatch: {row.get(status_col, '')}",
            evidence=[f"Status={row.get(status_col, '')}"],
            recommendation="Verify PF contributions. File revised ECR if needed.",
            priority=Priority.HIGH.value, department="compliance",
        ))
    return cases


def detect_missing_in_ecr(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    missing = sources.get("missing")
    if missing is None or missing.empty:
        return cases

    if "missing_from" in missing.columns:
        ecr_missing = missing[missing["missing_from"].astype(str).str.lower().str.contains("ecr|pf")]
        for _, row in ecr_missing.iterrows():
            name = str(row.get("employee_name", ""))
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.MISSING_IN_ECR.value,
                entity_name=name,
                risk_level=RiskLevel.HIGH.value,
                fraud_score=75.0, confidence=90.0,
                reason=f"Employee {name} missing from ECR/PF records",
                evidence=["Present in wages", "Missing in ECR"],
                recommendation="Add to ECR immediately. Check for arrears.",
                priority=Priority.HIGH.value, department="compliance",
            ))
    return cases


# ============================================================
# MODULE 11 — ESI FRAUD INTELLIGENCE
# ============================================================


def detect_esi_evasion(sources: Dict[str, pd.DataFrame], config: FraudConfig) -> List[FraudCase]:
    cases = []
    df = sources.get("esi")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    status_col = col_map.get("match_status")
    name_col = col_map.get("employee_name")

    if not status_col:
        return cases

    for _, row in df[df[status_col].astype(str).str.lower() != "matched"].iterrows():
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.ESI_EVASION.value,
            entity_name=str(row.get(name_col, "")) if name_col else "",
            risk_level=RiskLevel.HIGH.value,
            fraud_score=70.0, confidence=80.0,
            reason="ESI reconciliation mismatch",
            evidence=[f"Status={row.get(status_col, '')}"],
            recommendation="Verify ESI contributions and eligibility. File revised return.",
            priority=Priority.HIGH.value, department="compliance",
        ))
    return cases


def wrong_esi_threshold(sources: Dict[str, pd.DataFrame], config: FraudConfig) -> List[FraudCase]:
    """Detect ESI deducted for employees above wage limit."""
    cases = []
    df = sources.get("esi")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    elig_col = col_map.get("esi_eligibility")
    name_col = col_map.get("employee_name")
    emp_esi_col = col_map.get("employee_esi")

    if not elig_col:
        return cases

    for _, row in df.iterrows():
        elig = str(row.get(elig_col, "")).lower()
        actual = pd.to_numeric(row.get(emp_esi_col, 0), errors="coerce") or 0 if emp_esi_col else 0
        if elig == "not applicable" and actual > 0:
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.WRONG_ESI_THRESHOLD.value,
                entity_name=str(row.get(name_col, "")) if name_col else "",
                risk_level=RiskLevel.MEDIUM.value,
                fraud_score=60.0, confidence=90.0,
                reason=f"ESI deducted (₹{actual}) for non-eligible employee",
                evidence=[f"Eligibility=Not Applicable", f"ESI deducted={actual}"],
                recommendation="Remove ESI deduction. Refund to employee.",
                priority=Priority.MEDIUM.value, department="payroll",
            ))
    return cases


# ============================================================
# MODULE 12 — BANK FRAUD
# ============================================================


def detect_duplicate_payment(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("bank")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    acct_col = col_map.get("bank_account")
    name_col = col_map.get("employee_name")

    if not acct_col or acct_col not in df.columns:
        return cases

    dup_mask = df[acct_col].dropna().duplicated(keep=False)
    for _, row in df[dup_mask].iterrows():
        cases.append(FraudCase(
            case_id=generate_case_id(),
            fraud_type=FraudType.DUPLICATE_PAYMENT.value,
            entity_name=str(row.get(name_col, "")) if name_col else "",
            risk_level=RiskLevel.HIGH.value,
            fraud_score=80.0, confidence=90.0,
            reason=f"Duplicate bank account: {row.get(acct_col, '')}",
            evidence=[f"Bank account={row.get(acct_col, '')}"],
            recommendation="Verify bank account ownership. Possible duplicate payment.",
            priority=Priority.HIGH.value, department="finance",
        ))
    return cases


def detect_cash_payment(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    """Flag if bank file exists but employees have no bank records."""
    cases = []
    pay_df = sources.get("payroll")
    bank_df = sources.get("bank")
    if pay_df is None or pay_df.empty or bank_df is None or bank_df.empty:
        return cases

    pay_map = build_column_map(pay_df)
    bank_map = build_column_map(bank_df)
    p_name = pay_map.get("employee_name")
    b_name = bank_map.get("employee_name")

    if not p_name or not b_name:
        return cases

    bank_names = set(bank_df[b_name].dropna().astype(str).str.upper().str.strip())
    for _, row in pay_df.iterrows():
        name = str(row.get(p_name, "")).upper().strip()
        net_col = pay_map.get("net_pay")
        net = pd.to_numeric(row.get(net_col, 0), errors="coerce") or 0 if net_col else 0
        if name and name not in bank_names and net > 0:
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.CASH_PAYMENT.value,
                entity_name=name,
                risk_level=RiskLevel.MEDIUM.value,
                fraud_score=50.0, confidence=60.0,
                reason=f"Salary ₹{net:,.0f} paid but no bank transfer record",
                evidence=[f"Net pay={net}", "Not in bank records"],
                recommendation="Verify payment method. Cash payments should be documented.",
                priority=Priority.MEDIUM.value, department="finance",
            ))
    return cases


# ============================================================
# MODULE 13 — SITE ASSIGNMENT FRAUD
# ============================================================


def detect_double_site_assignment(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("site_assignments")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    date_col = col_map.get("date")
    site_col = col_map.get("site_location")
    name_col = col_map.get("employee_name")

    if not id_col or not date_col or not site_col:
        return cases

    grouped = df.groupby([id_col, date_col])
    for (eid, date), group in grouped:
        sites = group[site_col].dropna().unique()
        if len(sites) > 1:
            name = str(group.iloc[0].get(name_col, "")) if name_col else str(eid)
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.DOUBLE_SITE.value,
                entity_id=str(eid), entity_name=name,
                risk_level=RiskLevel.HIGH.value,
                fraud_score=75.0, confidence=90.0,
                reason=f"Assigned to {len(sites)} sites on {date}: {', '.join(str(s) for s in sites)}",
                evidence=[f"Date={date}", f"Sites={list(sites)}"],
                recommendation="Verify assignment. Guard cannot be at two sites simultaneously.",
                priority=Priority.HIGH.value, department="operations",
            ))
    return cases


def detect_unassigned_guard(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    guard_df = sources.get("guards")
    assign_df = sources.get("site_assignments")
    if guard_df is None or guard_df.empty or assign_df is None or assign_df.empty:
        return cases

    g_map = build_column_map(guard_df)
    a_map = build_column_map(assign_df)
    g_id = g_map.get("guard_id") or g_map.get("employee_id")
    a_id = a_map.get("guard_id") or a_map.get("employee_id")
    g_name = g_map.get("employee_name")

    if not g_id or not a_id:
        return cases

    assigned = set(assign_df[a_id].dropna().astype(str).str.strip())
    for _, row in guard_df.iterrows():
        gid = str(row.get(g_id, "")).strip()
        if gid and gid not in assigned:
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.UNASSIGNED_GUARD.value,
                entity_id=gid,
                entity_name=str(row.get(g_name, "")) if g_name else gid,
                risk_level=RiskLevel.MEDIUM.value,
                fraud_score=40.0, confidence=70.0,
                reason="Guard in master list but no site assignment",
                evidence=["In guard master", "Not in site assignments"],
                recommendation="Assign to site or verify employment status.",
                priority=Priority.MEDIUM.value, department="operations",
            ))
    return cases


# ============================================================
# MODULE 14 — COMPLIANCE FRAUD
# ============================================================


def detect_compliance_fraud(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("compliance")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    name_col = col_map.get("employee_name")
    pv_col = col_map.get("police_verification")
    train_col = col_map.get("training_status")
    lic_col = col_map.get("license_expiry")

    today = pd.Timestamp.now()

    for _, row in df.iterrows():
        name = str(row.get(name_col, "")) if name_col else ""

        # Expired police verification
        if pv_col and str(row.get(pv_col, "")).lower() in ("expired", "no", "pending", "nan"):
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.EXPIRED_DOCUMENT.value,
                entity_name=name,
                risk_level=RiskLevel.MEDIUM.value,
                fraud_score=50.0, confidence=85.0,
                reason="Missing or expired police verification",
                evidence=[f"PV status={row.get(pv_col, '')}"],
                recommendation="Get police verification done immediately.",
                priority=Priority.HIGH.value, department="hr",
            ))

        # Missing training
        if train_col and str(row.get(train_col, "")).lower() in ("no", "pending", "nan", "incomplete"):
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.MISSING_TRAINING.value,
                entity_name=name,
                risk_level=RiskLevel.LOW.value,
                fraud_score=30.0, confidence=90.0,
                reason="Training not completed",
                evidence=[f"Training status={row.get(train_col, '')}"],
                recommendation="Schedule training immediately.",
                priority=Priority.MEDIUM.value, department="hr",
            ))

        # Expired license
        if lic_col and pd.notna(row.get(lic_col)):
            try:
                lic_date = pd.to_datetime(row.get(lic_col))
                if lic_date < today:
                    cases.append(FraudCase(
                        case_id=generate_case_id(),
                        fraud_type=FraudType.EXPIRED_DOCUMENT.value,
                        entity_name=name,
                        risk_level=RiskLevel.HIGH.value,
                        fraud_score=65.0, confidence=95.0,
                        reason=f"License expired on {lic_date.date()}",
                        evidence=[f"License expiry={lic_date.date()}"],
                        recommendation="Renew license immediately. Suspend deployment until renewed.",
                        priority=Priority.HIGH.value, department="compliance",
                    ))
            except Exception:
                pass

    return cases


# ============================================================
# MODULE 15 — INCIDENT & COMPLAINT INTELLIGENCE
# ============================================================


def detect_repeat_offender(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("incidents")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")
    type_col = col_map.get("incident_type")

    if not id_col:
        return cases

    freq = df.groupby(id_col).size()
    for eid, count in freq.items():
        if count >= 3:
            name = ""
            if name_col:
                matches = df[df[id_col] == eid][name_col].dropna()
                name = str(matches.iloc[0]) if not matches.empty else str(eid)
            types = []
            if type_col:
                types = df[df[id_col] == eid][type_col].dropna().unique().tolist()
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type=FraudType.REPEAT_OFFENDER.value,
                entity_id=str(eid), entity_name=name,
                risk_level=RiskLevel.HIGH.value if count >= 5 else RiskLevel.MEDIUM.value,
                fraud_score=min(count * 15, 100), confidence=85.0,
                reason=f"Repeat offender: {count} incidents ({', '.join(str(t) for t in types[:3])})",
                evidence=[f"Incident count={count}", f"Types={types[:3]}"],
                recommendation="Review employment. Consider reassignment or termination.",
                priority=Priority.HIGH.value, department="hr",
            ))
    return cases


def detect_repeat_complaints(sources: Dict[str, pd.DataFrame]) -> List[FraudCase]:
    cases = []
    df = sources.get("complaints")
    if df is None or df.empty:
        return cases

    col_map = build_column_map(df)
    id_col = col_map.get("guard_id") or col_map.get("employee_id")
    name_col = col_map.get("employee_name")
    type_col = col_map.get("complaint_type")

    if not id_col:
        return cases

    freq = df.groupby(id_col).size()
    for eid, count in freq.items():
        if count >= 3:
            name = ""
            if name_col:
                matches = df[df[id_col] == eid][name_col].dropna()
                name = str(matches.iloc[0]) if not matches.empty else str(eid)
            cases.append(FraudCase(
                case_id=generate_case_id(),
                fraud_type="repeat_complaints",
                entity_id=str(eid), entity_name=name,
                risk_level=RiskLevel.MEDIUM.value,
                fraud_score=min(count * 10, 100), confidence=80.0,
                reason=f"Repeat complaints: {count} total",
                evidence=[f"Complaint count={count}"],
                recommendation="Investigate complaint patterns. Consider reassignment.",
                priority=Priority.MEDIUM.value, department="operations",
            ))
    return cases


# ============================================================
# MODULE 16 — AI ANOMALY DETECTION
# ============================================================


def ml_anomaly_detection(sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Statistical anomaly detection on payroll data."""
    df = sources.get("payroll")
    if df is None or df.empty:
        return pd.DataFrame()

    col_map = build_column_map(df)
    salary_col = col_map.get("basic_salary")
    name_col = col_map.get("employee_name")

    if not salary_col:
        return pd.DataFrame()

    values = pd.to_numeric(df[salary_col], errors="coerce").dropna()
    if len(values) < 10:
        return pd.DataFrame()

    mean, std = values.mean(), values.std()
    if std == 0:
        return pd.DataFrame()

    anomalies = []
    for idx, val in values.items():
        z = abs((val - mean) / std)
        if z > 3:
            name = str(df.loc[idx].get(name_col, "")) if name_col else ""
            anomalies.append({
                "employee_name": name,
                "value": float(val),
                "z_score": round(z, 2),
                "mean": round(mean, 2),
                "std": round(std, 2),
                "anomaly_type": "salary_outlier",
                "risk_level": "high" if z > 4 else "medium",
            })
    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


def feature_engineering(sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Prepare features for future ML models."""
    pay_df = sources.get("payroll")
    att_df = sources.get("attendance")

    if pay_df is None or pay_df.empty:
        return pd.DataFrame()

    pay_map = build_column_map(pay_df)
    name_col = pay_map.get("employee_name")
    salary_col = pay_map.get("basic_salary")
    ot_col = pay_map.get("overtime_hours")
    net_col = pay_map.get("net_pay")

    if not name_col:
        return pd.DataFrame()

    features = []
    for _, row in pay_df.iterrows():
        name = str(row.get(name_col, ""))
        salary = pd.to_numeric(row.get(salary_col, 0), errors="coerce") or 0
        ot = pd.to_numeric(row.get(ot_col, 0), errors="coerce") or 0
        net = pd.to_numeric(row.get(net_col, 0), errors="coerce") or 0

        features.append({
            "employee_name": name,
            "basic_salary": salary,
            "overtime_hours": ot,
            "net_pay": net,
            "ot_ratio": round(ot / max(salary, 1), 4),
            "deduction_ratio": round((salary - net) / max(salary, 1), 4),
        })

    return pd.DataFrame(features) if features else pd.DataFrame()


# ============================================================
# MODULE 17 — FRAUD CONFIDENCE
# ============================================================


def calculate_fraud_confidence(
    fraud_score: float, fraud_type_count: int, evidence_count: int,
) -> float:
    """How confident are we in this fraud detection?"""
    base = min(fraud_score * 0.6, 60)
    type_bonus = min(fraud_type_count * 10, 25)
    evidence_bonus = min(evidence_count * 5, 15)
    total = base + type_bonus + evidence_bonus
    return round(min(max(total, 10), 99.9), 1)


def confidence_score(confidence: float) -> str:
    if confidence >= 90:
        return "very_high"
    elif confidence >= 75:
        return "high"
    elif confidence >= 50:
        return "medium"
    elif confidence >= 30:
        return "low"
    return "very_low"


# ============================================================
# MODULE 18 — ROOT CAUSE ANALYSIS
# ============================================================


def find_root_cause(fraud_case: FraudCase) -> Dict[str, str]:
    """Determine root cause of a fraud case."""
    ft = fraud_case.fraud_type

    root_causes = {
        FraudType.GHOST_EMPLOYEE.value: {
            "root_cause": "Employee exists in payroll but has no verifiable presence",
            "evidence_chain": "Payroll record → No attendance → No bank transfer → No site assignment",
            "recommendation": "Suspend payment, conduct physical verification, check all documents",
            "resolution": "Immediate payroll suspension pending investigation",
        },
        FraudType.FAKE_ATTENDANCE.value: {
            "root_cause": "Attendance data manipulated — marked absent but hours recorded",
            "evidence_chain": "Status=Absent + Hours>0 → Data inconsistency",
            "recommendation": "Cross-check with biometric data, GPS logs, supervisor verification",
            "resolution": "Correct attendance records, recover excess payment",
        },
        FraudType.SALARY_INFLATION.value: {
            "root_cause": "Salary significantly above market/average without authorization",
            "evidence_chain": "Salary > 2x average → No revision approval → Possible collusion",
            "recommendation": "Verify salary revision documentation, check approval chain",
            "resolution": "Correct salary, recover excess paid",
        },
        FraudType.DUPLICATE_UAN.value: {
            "root_cause": "Same UAN assigned to multiple employees — possible identity fraud",
            "evidence_chain": "UAN lookup → Multiple employees → Identity sharing",
            "recommendation": "Verify each employee's UAN with EPFO portal",
            "resolution": "Assign correct unique UANs, file corrections",
        },
        FraudType.GPS_MISMATCH.value: {
            "root_cause": "Employee check-in location doesn't match assigned site",
            "evidence_chain": "GPS coordinates ≠ Site coordinates → Location fraud",
            "recommendation": "Verify physical presence, check GPS device integrity",
            "resolution": "Issue warning, deploy to correct location",
        },
    }

    return root_causes.get(ft, {
        "root_cause": fraud_case.reason,
        "evidence_chain": "; ".join(fraud_case.evidence),
        "recommendation": fraud_case.recommendation,
        "resolution": "Manual investigation required",
    })


def build_evidence(fraud_case: FraudCase) -> Dict[str, Any]:
    """Build structured evidence package."""
    root = find_root_cause(fraud_case)
    return {
        "case_id": fraud_case.case_id,
        "fraud_type": fraud_case.fraud_type,
        "entity": fraud_case.entity_name,
        "risk_level": fraud_case.risk_level,
        "fraud_score": fraud_case.fraud_score,
        "confidence": fraud_case.confidence,
        "root_cause": root.get("root_cause", ""),
        "evidence_chain": root.get("evidence_chain", ""),
        "evidence_points": fraud_case.evidence,
        "recommendation": root.get("recommendation", ""),
        "resolution": root.get("resolution", ""),
    }


def recommend_resolution(score: float, fraud_types: List[str], is_ghost: bool) -> str:
    if is_ghost:
        return "Suspend payment immediately. Conduct physical verification."
    if score > 80:
        return "Immediate investigation. Suspend pending verification."
    if score > 60:
        return "Priority investigation within 48 hours."
    if score > 40:
        return "Schedule investigation within 1 week."
    return "Monitor. Review in next payroll cycle."


# ============================================================
# MODULE 19 — FRAUD DASHBOARD
# ============================================================


def build_dashboard(
    all_cases: List[FraudCase],
    employee_scores: List[EmployeeFraudScore],
    site_frauds: List[SiteFraud],
    stats: RuntimeStats,
) -> Dict[str, Any]:
    """Build comprehensive fraud dashboard."""
    risk_dist = defaultdict(int)
    type_dist = defaultdict(int)
    for fc in all_cases:
        risk_dist[fc.risk_level] += 1
        type_dist[fc.fraud_type] += 1

    emp_risk_dist = defaultdict(int)
    for es in employee_scores:
        emp_risk_dist[es.risk_level] += 1

    return {
        "generated_at": datetime.now().isoformat(),
        "engine_version": "6.0.0",
        "summary": {
            "total_fraud_cases": len(all_cases),
            "total_employees_analyzed": len(employee_scores),
            "total_sites_analyzed": len(site_frauds),
            "ghost_employees": sum(1 for fc in all_cases if fc.fraud_type == FraudType.GHOST_EMPLOYEE.value),
            "critical_cases": risk_dist.get("critical", 0),
            "high_cases": risk_dist.get("high", 0),
            "medium_cases": risk_dist.get("medium", 0),
            "low_cases": risk_dist.get("low", 0),
        },
        "fraud_type_distribution": dict(type_dist),
        "risk_distribution": dict(risk_dist),
        "employee_risk_distribution": dict(emp_risk_dist),
        "top_fraud_types": sorted(type_dist.items(), key=lambda x: x[1], reverse=True)[:10],
        "runtime": stats.summary(),
    }


def fraud_summary(dashboard: Dict) -> Dict[str, Any]:
    return {
        "total_cases": dashboard["summary"]["total_fraud_cases"],
        "critical": dashboard["summary"]["critical_cases"],
        "high": dashboard["summary"]["high_cases"],
        "ghost": dashboard["summary"]["ghost_employees"],
    }


def fraud_distribution(dashboard: Dict) -> Dict[str, int]:
    return dashboard.get("fraud_type_distribution", {})


# ============================================================
# MODULE 20 — SITE / CLIENT HEATMAP
# ============================================================


def site_heatmap(site_frauds: List[SiteFraud]) -> pd.DataFrame:
    if not site_frauds:
        return pd.DataFrame()
    rows = []
    for sf in sorted(site_frauds, key=lambda s: s.fraud_score, reverse=True):
        rows.append({
            "site": sf.site_name,
            "client": sf.client,
            "total_employees": sf.total_employees,
            "fraud_count": sf.fraud_count,
            "fraud_score": sf.fraud_score,
            "risk_level": sf.risk_level,
            "ghost_count": sf.ghost_count,
            "attendance_fraud": sf.attendance_fraud,
            "payroll_fraud": sf.payroll_fraud,
            "identity_fraud": sf.identity_fraud,
            "rank": sf.rank,
        })
    return pd.DataFrame(rows)


def client_heatmap(client_data: List[Dict]) -> pd.DataFrame:
    return pd.DataFrame(client_data) if client_data else pd.DataFrame()


# ============================================================
# MODULE 21 — INVESTIGATION QUEUE
# ============================================================


def generate_investigation_queue(
    all_cases: List[FraudCase],
) -> List[InvestigationCase]:
    """Create prioritized investigation queue."""
    cases = []
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_cases = sorted(all_cases, key=lambda c: (priority_order.get(c.priority, 9), -c.fraud_score))

    for fc in sorted_cases:
        if fc.risk_level in ("safe", "low") and fc.fraud_score < 30:
            continue
        due_days = 1 if fc.priority == "critical" else (
            3 if fc.priority == "high" else 7
        )
        due = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")
        cases.append(InvestigationCase(
            case_id=fc.case_id,
            employee_name=fc.entity_name,
            site=fc.site,
            fraud_type=fc.fraud_type,
            risk_level=fc.risk_level,
            priority=fc.priority,
            assigned_to=assign_case_owner(fc),
            evidence="; ".join(fc.evidence[:3]),
            recommendation=fc.recommendation,
            due_date=due,
        ))
    return cases


def assign_case_owner(fc: FraudCase) -> str:
    """Assign investigation based on department."""
    dept_owners = {
        "hr": "HR Manager",
        "payroll": "Payroll Officer",
        "compliance": "Compliance Officer",
        "finance": "Finance Manager",
        "operations": "Operations Manager",
    }
    return dept_owners.get(fc.department, "Compliance Officer")


def assign_case_priority(fc: FraudCase) -> str:
    if fc.fraud_score > 80 or fc.risk_level == "critical":
        return Priority.CRITICAL.value
    if fc.fraud_score > 60 or fc.risk_level == "high":
        return Priority.HIGH.value
    if fc.fraud_score > 40:
        return Priority.MEDIUM.value
    return Priority.LOW.value


# ============================================================
# MODULE 22 — AUDIT TRAIL
# ============================================================


def fraud_history(all_cases: List[FraudCase]) -> pd.DataFrame:
    if not all_cases:
        return pd.DataFrame()
    return pd.DataFrame([asdict(fc) for fc in all_cases])


def processing_statistics(stats: RuntimeStats) -> Dict[str, Any]:
    return stats.summary()


# ============================================================
# MODULE 23 — EXPORT ENGINE
# ============================================================


def export_csv(reports: Dict[str, pd.DataFrame]):
    for name, df in reports.items():
        if df is not None and not df.empty:
            path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            logger.info(f"CSV → {path} ({len(df)} rows)")


def export_excel(reports: Dict[str, pd.DataFrame]):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"fraud_detection_report_{ts}.xlsx"
    sheets = {k[:31]: v for k, v in reports.items() if v is not None and not v.empty}
    if not sheets:
        return
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sn, df in sheets.items():
            df.to_excel(writer, sheet_name=sn, index=False)
    logger.info(f"Excel → {path} ({len(sheets)} sheets)")


def export_json(dashboard: Dict, stats: RuntimeStats):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {**dashboard, "runtime_stats": stats.summary()}
    path = SUMMARY_DIR / f"fraud_summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"JSON → {path}")


# ============================================================
# MODULE 2 — MULTI-SITE FRAUD DETECTION
# ============================================================


def calculate_site_fraud_score(
    all_cases: List[FraudCase],
    config: FraudConfig,
) -> List[SiteFraud]:
    site_data: Dict[str, List[FraudCase]] = defaultdict(list)
    for fc in all_cases:
        site = fc.site or "UNKNOWN"
        site_data[site].append(fc)

    site_frauds = []
    for site, cases in site_data.items():
        sf = SiteFraud(
            site_name=site,
            total_employees=len(set(fc.entity_id for fc in cases if fc.entity_id)),
            fraud_count=len(cases),
            fraud_score=min(sum(fc.fraud_score for fc in cases) / max(len(cases), 1), 100),
            ghost_count=sum(1 for fc in cases if fc.fraud_type == FraudType.GHOST_EMPLOYEE.value),
            attendance_fraud=sum(1 for fc in cases if "attendance" in fc.fraud_type or "shift" in fc.fraud_type),
            payroll_fraud=sum(1 for fc in cases if "salary" in fc.fraud_type or "overtime" in fc.fraud_type or "payroll" in fc.fraud_type),
            identity_fraud=sum(1 for fc in cases if "duplicate" in fc.fraud_type or "identity" in fc.fraud_type),
        )
        sf.risk_level = classify_fraud_risk(sf.fraud_score, config)
        site_frauds.append(sf)

    sorted_sf = sorted(site_frauds, key=lambda s: s.fraud_score, reverse=True)
    for i, s in enumerate(sorted_sf):
        s.rank = i + 1

    return sorted_sf


def rank_sites_by_fraud(site_frauds: List[SiteFraud]) -> List[SiteFraud]:
    return sorted(site_frauds, key=lambda s: s.fraud_count, reverse=True)


# ============================================================
# MODULE 3 — CLIENT-WISE FRAUD ANALYSIS
# ============================================================


def calculate_client_risk(
    site_frauds: List[SiteFraud],
) -> List[Dict[str, Any]]:
    client_data: Dict[str, List[SiteFraud]] = defaultdict(list)
    for sf in site_frauds:
        client_data[sf.client or "default"].append(sf)

    results = []
    for client, sites in client_data.items():
        total_emps = sum(s.total_employees for s in sites)
        total_fraud = sum(s.fraud_count for s in sites)
        avg_score = np.mean([s.fraud_score for s in sites]) if sites else 0
        results.append({
            "client": client,
            "total_sites": len(sites),
            "total_employees": total_emps,
            "total_fraud_cases": total_fraud,
            "avg_fraud_score": round(float(avg_score), 1),
            "risk_level": classify_fraud_risk(avg_score, FraudConfig()),
        })
    return sorted(results, key=lambda x: x["avg_fraud_score"], reverse=True)


def top_risky_clients(client_risks: List[Dict], n: int = 5) -> List[Dict]:
    return client_risks[:n]


# ============================================================
# MODULE 4 — MONTHLY FRAUD TREND
# ============================================================


def monthly_fraud_summary(
    all_cases: List[FraudCase],
) -> Dict[str, int]:
    month_dist = defaultdict(int)
    for fc in all_cases:
        try:
            dt = datetime.fromisoformat(fc.detected_at)
            key = dt.strftime("%Y-%m")
            month_dist[key] += 1
        except Exception:
            pass
    return dict(month_dist)


def compare_previous_month(
    current_cases: List[FraudCase],
    previous_file: Optional[Path] = None,
) -> Dict[str, Any]:
    if previous_file is None or not previous_file.exists():
        return {"status": "no_previous_data"}
    prev_df = pd.read_csv(previous_file)
    if prev_df.empty:
        return {"status": "no_previous_data"}
    prev_count = len(prev_df)
    curr_count = len(current_cases)
    return {
        "current_month": curr_count,
        "previous_month": prev_count,
        "change": curr_count - prev_count,
        "change_pct": round(((curr_count - prev_count) / max(prev_count, 1)) * 100, 1),
        "trend": "increasing" if curr_count > prev_count else (
            "decreasing" if curr_count < prev_count else "stable"
        ),
    }


def fraud_trend_analysis(monthly: Dict[str, int]) -> pd.DataFrame:
    if not monthly:
        return pd.DataFrame()
    rows = [{"month": k, "fraud_count": v} for k, v in sorted(monthly.items())]
    df = pd.DataFrame(rows)
    if len(df) >= 2:
        df["trend"] = df["fraud_count"].diff().apply(
            lambda x: "increasing" if x and x > 0 else ("decreasing" if x and x < 0 else "stable")
        )
    return df


# ============================================================
# MAIN ENGINE
# ============================================================


class FraudDetectionEngine:
    """
    Production fraud detection engine.
    Runs all 25 modules in sequence.
    """

    def __init__(
        self,
        config: Optional[FraudConfig] = None,
        client_name: str = "default",
    ):
        self.config = config or load_config()
        self.client_config = ClientConfig(client_name=client_name)
        self.stats = RuntimeStats()

        self.sources: Dict[str, pd.DataFrame] = {}
        self.all_cases: List[FraudCase] = []
        self.employee_scores: List[EmployeeFraudScore] = []
        self.site_frauds: List[SiteFraud] = []
        self.investigation_queue: List[InvestigationCase] = []
        self.dashboard: Dict[str, Any] = {}

        _audit_log.clear()
        global _case_counter
        _case_counter = 0

    def run(self) -> Dict[str, Any]:
        self.stats = RuntimeStats()
        cfg = self.config

        logger.info("=" * 70)
        logger.info("FRAUD DETECTION ENGINE")
        logger.info(f"Engine version: {cfg.engine_version}")
        logger.info("=" * 70)

        # ── 1. Load data ──
        logger.info("PHASE 1: LOADING DATA")
        self.sources = load_all_sources()
        self.stats.files_loaded = len(self.sources)
        for k, df in self.sources.items():
            self.stats.rows_loaded += len(df)
        audit_log("ENGINE_START", module="loader", detail=f"Loaded {len(self.sources)} sources")

        # ── 2. Run all detectors ──
        logger.info("PHASE 2: FRAUD DETECTION")

        all_cases = []
        module_count = 0

        # Attendance fraud
        logger.info("  Module 6: Attendance Fraud")
        all_cases.extend(detect_ghost_employees(self.sources))
        all_cases.extend(detect_fake_attendance(self.sources))
        all_cases.extend(detect_double_shift(self.sources))
        all_cases.extend(detect_impossible_hours(self.sources, cfg))
        all_cases.extend(detect_missing_checkout(self.sources))
        all_cases.extend(gps_mismatch_frequency(self.sources))
        module_count += 6

        # Payroll fraud
        logger.info("  Module 7: Payroll Fraud")
        all_cases.extend(detect_overtime_fraud(self.sources, cfg))
        all_cases.extend(detect_salary_inflation(self.sources, cfg))
        all_cases.extend(detect_salary_splitting(self.sources, cfg))
        all_cases.extend(detect_negative_deduction(self.sources))
        module_count += 4

        # Ghost employee intelligence
        logger.info("  Module 8: Ghost Employee Intelligence")
        all_cases.extend(inactive_employee_detection(self.sources))
        module_count += 1

        # Identity fraud — FIXED functions using _safe_get_df
        logger.info("  Module 9: Identity Fraud")
        all_cases.extend(duplicate_uan(self.sources))
        all_cases.extend(duplicate_ip(self.sources))
        all_cases.extend(duplicate_bank_account(self.sources))
        all_cases.extend(duplicate_pan(self.sources))
        all_cases.extend(duplicate_aadhaar(self.sources))
        module_count += 5

        # PF fraud
        logger.info("  Module 10: PF Fraud")
        all_cases.extend(detect_pf_evasion(self.sources))
        all_cases.extend(detect_missing_in_ecr(self.sources))
        module_count += 2

        # ESI fraud
        logger.info("  Module 11: ESI Fraud")
        all_cases.extend(detect_esi_evasion(self.sources, cfg))
        all_cases.extend(wrong_esi_threshold(self.sources, cfg))
        module_count += 2

        # Bank fraud
        logger.info("  Module 12: Bank Fraud")
        all_cases.extend(detect_duplicate_payment(self.sources))
        all_cases.extend(detect_cash_payment(self.sources))
        module_count += 2

        # Site assignment fraud
        logger.info("  Module 13: Site Assignment Fraud")
        all_cases.extend(detect_double_site_assignment(self.sources))
        all_cases.extend(detect_unassigned_guard(self.sources))
        module_count += 2

        # Compliance fraud
        logger.info("  Module 14: Compliance Fraud")
        all_cases.extend(detect_compliance_fraud(self.sources))
        module_count += 1

        # Incident & complaint
        logger.info("  Module 15: Incident & Complaint")
        all_cases.extend(detect_repeat_offender(self.sources))
        all_cases.extend(detect_repeat_complaints(self.sources))
        module_count += 2

        # AI anomaly
        logger.info("  Module 16: AI Anomaly Detection")
        anomalies = ml_anomaly_detection(self.sources)
        if not anomalies.empty:
            for _, row in anomalies.iterrows():
                all_cases.append(FraudCase(
                    case_id=generate_case_id(),
                    fraud_type=FraudType.STATISTICAL_OUTLIER.value,
                    entity_name=str(row.get("employee_name", "")),
                    risk_level=str(row.get("risk_level", "medium")),
                    fraud_score=float(row.get("z_score", 0)) * 20,
                    confidence=85.0,
                    reason=f"Statistical outlier: z-score={row.get('z_score', 0)}",
                    evidence=[f"Value={row.get('value', 0)}", f"Mean={row.get('mean', 0)}"],
                    recommendation="Investigate salary anomaly. Verify with payroll records.",
                    priority=Priority.MEDIUM.value,
                ))
        module_count += 1

        self.all_cases = all_cases
        self.stats.fraud_cases_detected = len(all_cases)
        self.stats.modules_run = module_count

        # Count by type
        for fc in all_cases:
            if fc.fraud_type == FraudType.GHOST_EMPLOYEE.value:
                self.stats.ghost_employees += 1
            elif "attendance" in fc.fraud_type or "shift" in fc.fraud_type:
                self.stats.attendance_frauds += 1
            elif "salary" in fc.fraud_type or "overtime" in fc.fraud_type:
                self.stats.payroll_frauds += 1
            elif "duplicate" in fc.fraud_type and "uan" in fc.fraud_type:
                self.stats.identity_frauds += 1
            elif "pf" in fc.fraud_type:
                self.stats.pf_frauds += 1
            elif "esi" in fc.fraud_type:
                self.stats.esi_frauds += 1
            elif "bank" in fc.fraud_type or "payment" in fc.fraud_type:
                self.stats.bank_frauds += 1
            elif "expired" in fc.fraud_type or "training" in fc.fraud_type:
                self.stats.compliance_frauds += 1

        logger.info(f"Total fraud cases: {len(all_cases)}")
        audit_log("DETECTION_COMPLETE", module="all", detail=f"Cases={len(all_cases)}")

        # ── 3. Employee fraud scores ──
        logger.info("PHASE 3: EMPLOYEE FRAUD SCORING")
        emp_cases: Dict[str, List[FraudCase]] = defaultdict(list)
        for fc in all_cases:
            key = fc.entity_name or fc.entity_id
            if key:
                emp_cases[key].append(fc)

        for emp_key, cases in emp_cases.items():
            fc0 = cases[0]
            ghost = any(c.fraud_type == FraudType.GHOST_EMPLOYEE.value for c in cases)
            att_flags = sum(1 for c in cases if "attendance" in c.fraud_type or "shift" in c.fraud_type or "hours" in c.fraud_type)
            pay_flags = sum(1 for c in cases if "salary" in c.fraud_type or "overtime" in c.fraud_type)
            id_flags = sum(1 for c in cases if "duplicate" in c.fraud_type)
            pf_flags = sum(1 for c in cases if "pf" in c.fraud_type)
            esi_flags = sum(1 for c in cases if "esi" in c.fraud_type)
            bank_flags = sum(1 for c in cases if "bank" in c.fraud_type or "payment" in c.fraud_type)
            comp_flags = sum(1 for c in cases if "expired" in c.fraud_type or "training" in c.fraud_type)

            score = calculate_employee_fraud_score(
                employee_name=fc0.entity_name,
                employee_id=fc0.entity_id,
                site=fc0.site,
                sources=self.sources,
                config=cfg,
                ghost_flag=ghost,
                attendance_flags=att_flags,
                payroll_flags=pay_flags,
                identity_flags=id_flags,
                pf_flags=pf_flags,
                esi_flags=esi_flags,
                bank_flags=bank_flags,
                compliance_flags=comp_flags,
                fraud_types=list(set(c.fraud_type for c in cases)),
                evidence=[e for c in cases for e in c.evidence],
            )
            self.employee_scores.append(score)

        self.stats.employees_scored = len(self.employee_scores)
        logger.info(f"Employees scored: {len(self.employee_scores)}")

        # ── 4. Site fraud scores ──
        logger.info("PHASE 4: SITE FRAUD SCORING")
        self.site_frauds = calculate_site_fraud_score(all_cases, cfg)
        self.site_frauds = rank_sites_by_fraud(self.site_frauds)
        self.stats.sites_analyzed = len(self.site_frauds)

        # ── 5. Client analysis ──
        logger.info("PHASE 5: CLIENT ANALYSIS")
        client_risks = calculate_client_risk(self.site_frauds)

        # ── 6. Trend analysis ──
        logger.info("PHASE 6: TREND ANALYSIS")
        monthly = monthly_fraud_summary(all_cases)
        prev_file = OUTPUT_DIR / "fraud_history.csv"
        trend = compare_previous_month(all_cases, prev_file)
        trend_df = fraud_trend_analysis(monthly)

        # ── 7. Investigation queue ──
        logger.info("PHASE 7: INVESTIGATION QUEUE")
        self.investigation_queue = generate_investigation_queue(all_cases)
        self.stats.investigation_cases = len(self.investigation_queue)

        # ── 8. Dashboard ──
        logger.info("PHASE 8: DASHBOARD")
        self.dashboard = build_dashboard(all_cases, self.employee_scores, self.site_frauds, self.stats)

        # ── 9. Build evidence for top cases ──
        logger.info("PHASE 9: ROOT CAUSE & EVIDENCE")
        evidence_packages = []
        for fc in sorted(all_cases, key=lambda c: c.fraud_score, reverse=True)[:50]:
            evidence_packages.append(build_evidence(fc))

        # ── 10. Export ──
        logger.info("PHASE 10: EXPORT")
        self.stats.finish()
        audit_log("ENGINE_COMPLETE", detail=f"Elapsed={self.stats.elapsed}s")

        # Build DataFrames
        cases_df = pd.DataFrame([asdict(fc) for fc in all_cases]) if all_cases else pd.DataFrame()
        emp_df = pd.DataFrame([asdict(e) for e in self.employee_scores]) if self.employee_scores else pd.DataFrame()
        site_df = site_heatmap(self.site_frauds)
        inv_df = pd.DataFrame([asdict(i) for i in self.investigation_queue]) if self.investigation_queue else pd.DataFrame()
        evidence_df = pd.DataFrame(evidence_packages) if evidence_packages else pd.DataFrame()
        client_df = client_heatmap(client_risks)
        monthly_df = pd.DataFrame([{"month": k, "count": v} for k, v in sorted(monthly.items())]) if monthly else pd.DataFrame()
        audit_df = get_audit_dataframe()
        anomaly_df = anomalies if not anomalies.empty else pd.DataFrame()
        feature_df = feature_engineering(self.sources)

        all_reports = {
            "fraud_detection_report": cases_df,
            "employee_fraud_scores": emp_df,
            "site_fraud_heatmap": site_df,
            "client_fraud_analysis": client_df,
            "investigation_queue": inv_df,
            "evidence_packages": evidence_df,
            "monthly_trend": monthly_df,
            "trend_analysis": trend_df,
            "anomalies": anomaly_df,
            "ml_features": feature_df,
            "audit_trail": audit_df,
        }

        csv_reports = {k: v for k, v in all_reports.items() if v is not None and not v.empty}
        export_csv(csv_reports)
        export_excel(csv_reports)
        export_json(self.dashboard, self.stats)

        # Save history
        if not cases_df.empty:
            history_path = OUTPUT_DIR / "fraud_history.csv"
            cases_df.to_csv(history_path, index=False, encoding="utf-8-sig")

        # ── Final summary ──
        logger.info("=" * 70)
        logger.info("FRAUD DETECTION COMPLETE")
        logger.info(f"  Elapsed:          {self.stats.elapsed}s")
        logger.info(f"  Files loaded:     {self.stats.files_loaded}")
        logger.info(f"  Rows processed:   {self.stats.rows_loaded}")
        logger.info(f"  Modules run:      {self.stats.modules_run}")
        logger.info(f"  Fraud cases:      {self.stats.fraud_cases_detected}")
        logger.info(f"    Ghost:          {self.stats.ghost_employees}")
        logger.info(f"    Attendance:     {self.stats.attendance_frauds}")
        logger.info(f"    Payroll:        {self.stats.payroll_frauds}")
        logger.info(f"    Identity:       {self.stats.identity_frauds}")
        logger.info(f"    PF:             {self.stats.pf_frauds}")
        logger.info(f"    ESI:            {self.stats.esi_frauds}")
        logger.info(f"    Bank:           {self.stats.bank_frauds}")
        logger.info(f"    Compliance:     {self.stats.compliance_frauds}")
        logger.info(f"  Employees scored: {self.stats.employees_scored}")
        logger.info(f"  Sites analyzed:   {self.stats.sites_analyzed}")
        logger.info(f"  Investigation:    {self.stats.investigation_cases}")
        logger.info(f"  CSV files:        {len(csv_reports)}")
        logger.info("=" * 70)

        return self.dashboard


# ============================================================
# BACKWARD-COMPATIBLE run()
# ============================================================


def run_fraud_detection():
    """Legacy function — returns flat DataFrame."""
    engine = FraudDetectionEngine()
    result = engine.run()
    if engine.all_cases:
        return pd.DataFrame([asdict(fc) for fc in engine.all_cases])
    return pd.DataFrame([{"Fraud_Type": "No Fraud Detected", "entity_id": "N/A", "risk_level": "Safe"}])


def run():
    engine = FraudDetectionEngine()
    return engine.run()


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fraud Detection Engine")
    parser.add_argument("--client", default="default")
    parser.add_argument("--config", default=None)
    parser.add_argument("--operator", default="auto")

    args = parser.parse_args()
    cfg = load_config(Path(args.config) if args.config else None)
    cfg.operator = args.operator

    engine = FraudDetectionEngine(config=cfg, client_name=args.client)
    result = engine.run()
    print(json.dumps(result, indent=2, default=str))
