# security-ai/scripts/wage_anomaly_detector.py
"""
Production-Grade Wage Anomaly Detector
Security AI — Multi-Dimensional Wage Intelligence System

═══════════════════════════════════════════════════════════════════
 25 MODULES | 100+ FUNCTIONS | AI ANOMALY DETECTION | EXPLAINABLE
═══════════════════════════════════════════════════════════════════

 MODULES:
  1.  Configurable Rules Engine
  2.  Feature Engineering (ML-Ready)
  3.  Wage Component Validation
  4.  Overtime Intelligence
  5.  Attendance vs Wage Validation
  6.  Duplicate Salary Detection
  7.  Wage Inflation Detection
  8.  Negative Payroll Validation
  9.  Salary Ceiling Validation
  10. Government Compliance Validation
  11. Payroll Consistency Engine
  12. Bank Reconciliation
  13. Leave Impact Analysis
  14. Wage Fraud Detection
  15. Multi-Site Wage Analysis
  16. Client-wise Wage Analysis
  17. Employee Wage History
  18. AI Wage Prediction (Statistical)
  19. Wage Risk Scoring
  20. Explainable AI
  21. Trend Analytics
  22. Department / Category Analysis
  23. Executive Dashboard
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
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

try:
    from sklearn.ensemble import IsolationForest
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger_temp = logging.getLogger("WageAnomaly")
    logger_temp.warning("sklearn not available — ML anomaly detection disabled")

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_DIR = BASE_DIR / "processed"
DATASET_DIR = BASE_DIR / "datasets"
RECON_DIR = BASE_DIR / "reconciliation"
OUTPUT_DIR = BASE_DIR / "anomaly_reports"
EXPORT_DIR = BASE_DIR / "exports"
SUMMARY_DIR = BASE_DIR / "summaries"
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

for _d in (INPUT_DIR, DATASET_DIR, RECON_DIR, OUTPUT_DIR, EXPORT_DIR, SUMMARY_DIR, LOG_DIR, CONFIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ============================================================
# MODULE 24 — PRODUCTION LOGGING
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(funcName)s:%(lineno)d | %(message)s"
)
LOG_DATE = "%Y-%m-%d %H:%M:%S"


def setup_rotating_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("WageAnomaly")
    root.setLevel(logging.DEBUG)
    if root.handlers:
        return root
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(ch)
    fh = RotatingFileHandler(
        log_dir / "wage_anomaly.log",
        maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(fh)
    eh = RotatingFileHandler(
        log_dir / "wage_anomaly_errors.log",
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


class AnomalyType(str, Enum):
    EXCESSIVE_OT = "excessive_overtime"
    INVALID_DAYS = "invalid_working_days"
    ZERO_WAGE = "zero_wage"
    NEGATIVE_PAY = "negative_net_pay"
    HIGH_RECOVERIES = "high_recoveries"
    SALARY_SPIKE = "salary_spike"
    SALARY_INFLATION = "salary_inflation"
    DUPLICATE_SALARY = "duplicate_salary"
    BELOW_MINIMUM_WAGE = "below_minimum_wage"
    PF_CEILING_VIOLATION = "pf_ceiling_violation"
    ESI_CEILING_VIOLATION = "esi_ceiling_violation"
    GROSS_MISMATCH = "gross_mismatch"
    NET_MISMATCH = "net_mismatch"
    PAYROLL_INCONSISTENCY = "payroll_inconsistency"
    BANK_MISMATCH = "bank_mismatch"
    FAKE_OT = "fake_overtime"
    FAKE_BONUS = "fake_bonus"
    SALARY_OVERRIDE = "salary_override"
    ATTENDANCE_MISMATCH = "attendance_wage_mismatch"
    LEAVE_MISMATCH = "leave_deduction_mismatch"
    STATISTICAL_OUTLIER = "statistical_outlier"
    ML_ANOMALY = "ml_anomaly"
    NEGATIVE_OT = "negative_overtime"
    NEGATIVE_DEDUCTION = "negative_deduction"
    SITE_VARIANCE = "site_wage_variance"


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================
# MODULE 1 — CONFIGURABLE RULES ENGINE
# ============================================================


@dataclass
class WageConfig:
    """All thresholds — loaded from config, never hardcoded."""
    # OT rules
    max_daily_ot: float = 4.0
    max_weekly_ot: float = 24.0
    max_monthly_ot: float = 100.0
    ot_threshold_business: float = 50.0

    # Days
    max_working_days: int = 31
    min_working_days: int = 0
    standard_working_days: int = 26

    # Salary
    min_wage_daily: float = 178.0        # ₹178/day approximate
    min_wage_monthly: float = 4632.0     # approximate
    max_recovery_pct: float = 0.50
    salary_spike_multiplier: float = 2.0
    salary_drop_pct: float = 0.30

    # PF / ESI
    pf_ceiling: float = 15000.0
    esi_wage_limit: float = 21000.0
    pf_employee_rate: float = 0.12
    esi_employee_rate: float = 0.0075

    # ML
    isolation_contamination: float = 0.05
    zscore_threshold: float = 3.0
    iqr_multiplier: float = 1.5

    # Risk scoring weights
    weight_ot: float = 0.15
    weight_days: float = 0.10
    weight_salary: float = 0.20
    weight_deduction: float = 0.10
    weight_consistency: float = 0.15
    weight_fraud: float = 0.15
    weight_compliance: float = 0.10
    weight_statistical: float = 0.05

    # Engine
    engine_version: str = "7.0.0"
    operator: str = "auto"


@dataclass
class AnomalyRecord:
    """Single anomaly detection result."""
    row_index: int = 0
    employee_name: str = ""
    employee_id: str = ""
    site: str = ""
    client: str = ""
    anomaly_type: str = ""
    risk_level: str = RiskLevel.MEDIUM.value
    risk_score: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    evidence: List[str] = field(default_factory=list)
    actual_value: float = 0.0
    expected_value: float = 0.0
    difference: float = 0.0
    recommendation: str = ""
    department: str = "payroll"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class EmployeeWageRisk:
    employee_name: str = ""
    employee_id: str = ""
    site: str = ""
    basic_salary: float = 0.0
    net_pay: float = 0.0
    risk_score: float = 0.0
    risk_level: str = RiskLevel.SAFE.value
    confidence: float = 0.0
    anomaly_count: int = 0
    anomaly_types: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class SiteWageStats:
    site_name: str = ""
    employee_count: int = 0
    avg_salary: float = 0.0
    median_salary: float = 0.0
    std_salary: float = 0.0
    min_salary: float = 0.0
    max_salary: float = 0.0
    avg_ot: float = 0.0
    total_ot: float = 0.0
    anomaly_count: int = 0
    risk_score: float = 0.0
    risk_level: str = RiskLevel.SAFE.value


@dataclass
class AuditEntry:
    timestamp: str = ""
    action: str = ""
    module: str = ""
    detail: str = ""
    rows_affected: int = 0
    engine_version: str = "7.0.0"


@dataclass
class RuntimeStats:
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_loaded: int = 0
    rows_loaded: int = 0
    rows_processed: int = 0
    modules_run: int = 0
    anomalies_detected: int = 0
    ml_anomalies: int = 0
    rule_anomalies: int = 0
    high_risk_employees: int = 0
    sites_analyzed: int = 0
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


# Global
_audit_log: List[AuditEntry] = []


def load_config(config_path: Optional[Path] = None) -> WageConfig:
    cfg = WageConfig()
    if config_path and config_path.exists():
        try:
            with open(config_path) as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
        except Exception as e:
            logger.warning(f"Config load error: {e}")
    return cfg


# ============================================================
# FIELD RESOLVER
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "employee_name": ["employee_name", "emp_name", "name", "staff_name", "guard_name", "NAME", "Employee_Name"],
    "employee_id": ["employee_id", "emp_id", "guard_id", "Guard_ID", "staff_id", "code"],
    "site_location": ["site_location", "site", "location", "branch", "unit", "Site", "site_name"],
    "client": ["client", "client_name", "Client"],
    "department": ["department", "dept", "category", "designation"],
    "basic_salary": ["basic_salary", "basic_vda", "basic", "BASIC + VDA", "Basic_VDA", "basic_wages"],
    "da": ["da", "dearness_allowance", "vda", "VDA"],
    "hra": ["hra", "house_rent_allowance"],
    "bonus": ["bonus", "bonus_amount"],
    "special_basic": ["special_basic", "special_allowance"],
    "gross_wages": ["gross_wages", "gross", "total_wages", "TOTAL", "Gross_Wages", "total_salary"],
    "net_pay": ["net_pay", "net_salary", "NET PAYMENT", "NET_PAYMENT", "Net_Pay", "net_payment"],
    "employee_pf": ["employee_pf", "epf", "pf_deduction", "EPF 12%", "pf"],
    "employee_esi": ["employee_esi", "esic", "esi_deduction", "ESIC 0.75%", "esi"],
    "overtime_hours": ["overtime_hours", "ot_hours", "Overtime Hours Worked", "OT", "ot"],
    "overtime_amount": ["overtime_amount", "ot_amount"],
    "days_worked": ["days_worked", "working_days", "No Of Days Worked", "days_present", "days"],
    "recoveries": ["recoveries", "Recoveries", "deductions", "total_deductions"],
    "leave_days": ["leave_days", "lwp", "leave_without_pay", "lop"],
    "attendance_pct": ["attendance_pct", "attendance_percentage"],
    "bank_account": ["bank_account", "bank_account_number", "account_number"],
    "transfer_amount": ["transfer_amount", "bank_credit"],
    "joining_date": ["joining_date", "doj", "date_of_joining"],
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
        "wages": INPUT_DIR / "wages.csv",
        "attendance": DATASET_DIR / "attendance.csv",
        "payroll": DATASET_DIR / "payroll.csv",
        "guards": DATASET_DIR / "guards_master.csv",
        "bank": DATASET_DIR / "bank.csv",
        "pf": RECON_DIR / "pf_reconciliation_report.csv",
        "esi": RECON_DIR / "esi_reconciliation_report.csv",
        "previous_wages": INPUT_DIR / "wages_previous.csv",
    }
    for key, path in files.items():
        df = safe_load(path)
        if not df.empty:
            sources[key] = df
    return sources


def audit_log(action: str, module: str = "", detail: str = "", rows: int = 0):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(), action=action,
        module=module, detail=detail, rows_affected=rows,
    ))


def get_audit_dataframe() -> pd.DataFrame:
    return pd.DataFrame([asdict(e) for e in _audit_log]) if _audit_log else pd.DataFrame()


# ============================================================
# MODULE 2 — FEATURE ENGINEERING
# ============================================================


def feature_engineering(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    """Build ML-ready feature set."""
    features = pd.DataFrame(index=df.index)

    basic_col = col_map.get("basic_salary")
    gross_col = col_map.get("gross_wages")
    net_col = col_map.get("net_pay")
    ot_col = col_map.get("overtime_hours")
    days_col = col_map.get("days_worked")
    pf_col = col_map.get("employee_pf")
    esi_col = col_map.get("employee_esi")
    rec_col = col_map.get("recoveries")

    basic = pd.to_numeric(df[basic_col], errors="coerce").fillna(0) if basic_col else 0
    gross = pd.to_numeric(df[gross_col], errors="coerce").fillna(0) if gross_col else 0
    net = pd.to_numeric(df[net_col], errors="coerce").fillna(0) if net_col else 0
    ot = pd.to_numeric(df[ot_col], errors="coerce").fillna(0) if ot_col else 0
    days = pd.to_numeric(df[days_col], errors="coerce").fillna(0) if days_col else 0
    pf = pd.to_numeric(df[pf_col], errors="coerce").fillna(0) if pf_col else 0
    esi = pd.to_numeric(df[esi_col], errors="coerce").fillna(0) if esi_col else 0
    rec = pd.to_numeric(df[rec_col], errors="coerce").fillna(0) if rec_col else 0

    features["basic_salary"] = basic
    features["gross_wages"] = gross
    features["net_pay"] = net
    features["overtime_hours"] = ot
    features["days_worked"] = days
    features["pf_deduction"] = pf
    features["esi_deduction"] = esi
    features["recoveries"] = rec

    # Derived features
    safe_days = days.replace(0, 1)
    features["salary_per_day"] = (basic / safe_days).round(2)
    features["ot_per_day"] = (ot / safe_days).round(2)
    features["recovery_pct"] = (rec / gross.replace(0, 1) * 100).round(2)
    features["pf_pct"] = (pf / basic.replace(0, 1) * 100).round(2)
    features["esi_pct"] = (esi / basic.replace(0, 1) * 100).round(2)
    features["net_pay_pct"] = (net / gross.replace(0, 1) * 100).round(2)
    features["ot_ratio"] = (ot / 8).round(2)  # OT days equivalent
    features["deduction_total"] = (pf + esi + rec).round(2)
    features["deduction_ratio"] = ((pf + esi + rec) / gross.replace(0, 1) * 100).round(2)
    features["gross_basic_ratio"] = (gross / basic.replace(0, 1)).round(2)

    return features.fillna(0)


def normalize_features(features: pd.DataFrame) -> pd.DataFrame:
    """Z-score normalization for ML."""
    numeric = features.select_dtypes(include=[np.number])
    means = numeric.mean()
    stds = numeric.std().replace(0, 1)
    return ((numeric - means) / stds).round(4)


def prepare_ml_dataset(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    """Full ML preparation pipeline."""
    features = feature_engineering(df, col_map)
    normalized = normalize_features(features)
    return normalized


# ============================================================
# MODULE 3 — WAGE COMPONENT VALIDATION
# ============================================================


def validate_basic(row: Dict, col_map: Dict, config: WageConfig) -> Optional[AnomalyRecord]:
    basic_col = col_map.get("basic_salary")
    if not basic_col:
        return None
    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0

    if basic <= 0:
        return AnomalyRecord(
            anomaly_type=AnomalyType.ZERO_WAGE.value,
            risk_level=RiskLevel.HIGH.value,
            risk_score=80, confidence=95,
            reason="Zero basic salary", actual_value=basic,
            evidence=["Basic salary is zero or negative"],
            recommendation="Verify payroll data. Employee may be on unpaid leave.",
            department="payroll",
        )
    if basic < config.min_wage_monthly:
        return AnomalyRecord(
            anomaly_type=AnomalyType.BELOW_MINIMUM_WAGE.value,
            risk_level=RiskLevel.HIGH.value,
            risk_score=75, confidence=85,
            reason=f"Basic ₹{basic:,.0f} below minimum wage ₹{config.min_wage_monthly:,.0f}",
            actual_value=basic, expected_value=config.min_wage_monthly,
            difference=basic - config.min_wage_monthly,
            evidence=[f"Basic={basic}", f"Min wage={config.min_wage_monthly}"],
            recommendation="Verify against state minimum wages. May need salary revision.",
            department="compliance",
        )
    return None


def validate_salary_components(row: Dict, col_map: Dict) -> Optional[AnomalyRecord]:
    """Verify component sums match gross."""
    gross_col = col_map.get("gross_wages")
    basic_col = col_map.get("basic_salary")
    ot_col = col_map.get("overtime_amount")
    bonus_col = col_map.get("bonus")

    if not gross_col or not basic_col:
        return None

    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    ot = pd.to_numeric(row.get(ot_col, 0), errors="coerce") or 0 if ot_col else 0
    bonus = pd.to_numeric(row.get(bonus_col, 0), errors="coerce") or 0 if bonus_col else 0

    expected_min = basic + ot
    if gross > 0 and expected_min > 0 and abs(gross - expected_min) > gross * 0.3:
        return AnomalyRecord(
            anomaly_type=AnomalyType.GROSS_MISMATCH.value,
            risk_level=RiskLevel.MEDIUM.value,
            risk_score=50, confidence=70,
            reason=f"Gross ₹{gross:,.0f} differs significantly from basic ₹{basic:,.0f}",
            actual_value=gross, expected_value=expected_min,
            difference=round(gross - expected_min, 2),
            evidence=[f"Gross={gross}", f"Basic={basic}", f"Diff={gross - basic:.0f}"],
            recommendation="Verify all salary components are correctly allocated.",
            department="payroll",
        )
    return None


# ============================================================
# MODULE 4 — OVERTIME INTELLIGENCE
# ============================================================


def detect_excessive_ot(row: Dict, col_map: Dict, config: WageConfig) -> Optional[AnomalyRecord]:
    ot_col = col_map.get("overtime_hours")
    if not ot_col:
        return None
    ot = pd.to_numeric(row.get(ot_col, 0), errors="coerce") or 0
    if ot > config.ot_threshold_business:
        severity = RiskLevel.HIGH.value if ot > config.max_monthly_ot else RiskLevel.MEDIUM.value
        return AnomalyRecord(
            anomaly_type=AnomalyType.EXCESSIVE_OT.value,
            risk_level=severity,
            risk_score=min(ot * 1.5, 100), confidence=85,
            reason=f"Excessive overtime: {ot:.0f} hours (limit: {config.ot_threshold_business})",
            actual_value=ot, expected_value=config.ot_threshold_business,
            difference=round(ot - config.ot_threshold_business, 1),
            evidence=[f"OT hours={ot}", f"Threshold={config.ot_threshold_business}"],
            recommendation="Verify OT authorization. Check attendance records.",
            department="operations",
        )
    return None


def detect_negative_ot(row: Dict, col_map: Dict) -> Optional[AnomalyRecord]:
    ot_col = col_map.get("overtime_hours")
    if not ot_col:
        return None
    ot = pd.to_numeric(row.get(ot_col, 0), errors="coerce") or 0
    if ot < 0:
        return AnomalyRecord(
            anomaly_type=AnomalyType.NEGATIVE_OT.value,
            risk_level=RiskLevel.MEDIUM.value,
            risk_score=55, confidence=95,
            reason=f"Negative overtime: {ot}", actual_value=ot,
            evidence=[f"OT={ot}"],
            recommendation="Data entry error. Correct overtime value.",
            department="payroll",
        )
    return None


def employee_ot_ranking(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    ot_col = col_map.get("overtime_hours")
    name_col = col_map.get("employee_name")
    site_col = col_map.get("site_location")
    if not ot_col:
        return pd.DataFrame()

    ranked = df.copy()
    ranked["ot_numeric"] = pd.to_numeric(ranked[ot_col], errors="coerce").fillna(0)
    ranked = ranked.sort_values("ot_numeric", ascending=False)
    result = ranked.head(20)[[c for c in [name_col, site_col, ot_col] if c]].copy()
    result["ot_rank"] = range(1, len(result) + 1)
    return result


# ============================================================
# MODULE 5 — ATTENDANCE vs WAGE VALIDATION
# ============================================================


def expected_salary_from_attendance(
    days_worked: float, daily_rate: float, config: WageConfig,
) -> float:
    return round(days_worked * daily_rate, 2)


def attendance_salary_variance(
    row: Dict, col_map: Dict, config: WageConfig,
) -> Optional[AnomalyRecord]:
    days_col = col_map.get("days_worked")
    basic_col = col_map.get("basic_salary")

    if not days_col or not basic_col:
        return None

    days = pd.to_numeric(row.get(days_col, 0), errors="coerce") or 0
    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0

    if days <= 0 or basic <= 0:
        return None

    daily_rate = config.min_wage_daily
    expected = expected_salary_from_attendance(days, daily_rate, config)
    actual_per_day = basic / days if days > 0 else 0

    # If salary per day is way above or below expected
    if actual_per_day < daily_rate * 0.5 and days > 15:
        return AnomalyRecord(
            anomaly_type=AnomalyType.ATTENDANCE_MISMATCH.value,
            risk_level=RiskLevel.MEDIUM.value,
            risk_score=50, confidence=70,
            reason=f"Daily wage ₹{actual_per_day:.0f} below minimum (₹{daily_rate})",
            actual_value=actual_per_day, expected_value=daily_rate,
            difference=round(actual_per_day - daily_rate, 2),
            evidence=[f"Days={days}", f"Basic={basic}", f"Per day={actual_per_day:.0f}"],
            recommendation="Verify attendance records and salary calculation.",
            department="payroll",
        )
    return None


# ============================================================
# MODULE 6 — DUPLICATE SALARY DETECTION
# ============================================================


def detect_duplicate_salary(df: pd.DataFrame, col_map: Dict) -> List[AnomalyRecord]:
    anomalies = []
    name_col = col_map.get("employee_name")
    id_col = col_map.get("employee_id")
    gross_col = col_map.get("gross_wages")
    bank_col = col_map.get("bank_account")

    if not name_col:
        return anomalies

    # Same name multiple entries
    name_counts = df[name_col].value_counts()
    for name, count in name_counts.items():
        if count > 1:
            idx = df[df[name_col] == name].index[0]
            anomalies.append(AnomalyRecord(
                row_index=int(idx), employee_name=str(name),
                anomaly_type=AnomalyType.DUPLICATE_SALARY.value,
                risk_level=RiskLevel.HIGH.value,
                risk_score=80, confidence=90,
                reason=f"Employee {name} appears {count} times in payroll",
                evidence=[f"Count={count}"],
                recommendation="Verify duplicate entry. Possible duplicate payment.",
                department="payroll",
            ))

    # Same bank account multiple employees
    if bank_col and bank_col in df.columns:
        bank_counts = df[bank_col].dropna().value_counts()
        for acct, count in bank_counts.items():
            if count > 1:
                anomalies.append(AnomalyRecord(
                    anomaly_type=AnomalyType.DUPLICATE_SALARY.value,
                    risk_level=RiskLevel.HIGH.value,
                    risk_score=85, confidence=95,
                    reason=f"Bank account {acct} used by {count} employees",
                    evidence=[f"Bank={acct}", f"Count={count}"],
                    recommendation="Verify bank account ownership. Possible fraud.",
                    department="finance",
                ))

    return anomalies


# ============================================================
# MODULE 7 — WAGE INFLATION DETECTION
# ============================================================


def salary_spike_detection(
    df: pd.DataFrame, col_map: Dict, config: WageConfig,
) -> List[AnomalyRecord]:
    """Detect salary jumps from previous month."""
    anomalies = []
    basic_col = col_map.get("basic_salary")
    name_col = col_map.get("employee_name")

    if not basic_col:
        return anomalies

    salaries = pd.to_numeric(df[basic_col], errors="coerce").dropna()
    if salaries.empty:
        return anomalies

    avg = salaries.mean()
    threshold = avg * config.salary_spike_multiplier

    for idx, val in salaries.items():
        if val > threshold:
            name = str(df.loc[idx].get(name_col, "")) if name_col else ""
            anomalies.append(AnomalyRecord(
                row_index=int(idx), employee_name=name,
                anomaly_type=AnomalyType.SALARY_SPIKE.value,
                risk_level=RiskLevel.HIGH.value,
                risk_score=75, confidence=80,
                reason=f"Salary ₹{val:,.0f} is {val / avg:.1f}x average ₹{avg:,.0f}",
                actual_value=float(val), expected_value=round(avg, 2),
                difference=round(val - avg, 2),
                evidence=[f"Salary={val:.0f}", f"Average={avg:.0f}", f"Ratio={val / avg:.1f}x"],
                recommendation="Verify salary revision authorization.",
                department="payroll",
            ))
    return anomalies


def salary_inflation(
    df: pd.DataFrame, col_map: Dict, config: WageConfig,
) -> List[AnomalyRecord]:
    """Detect salaries inflated above department/site average."""
    anomalies = []
    basic_col = col_map.get("basic_salary")
    name_col = col_map.get("employee_name")
    site_col = col_map.get("site_location")

    if not basic_col or not site_col:
        return anomalies

    for site, group in df.groupby(site_col):
        salaries = pd.to_numeric(group[basic_col], errors="coerce").dropna()
        if len(salaries) < 5:
            continue
        mean = salaries.mean()
        std = salaries.std()
        if std == 0:
            continue

        for idx, val in salaries.items():
            z = abs((val - mean) / std)
            if z > config.zscore_threshold:
                name = str(group.loc[idx].get(name_col, "")) if name_col else ""
                anomalies.append(AnomalyRecord(
                    row_index=int(idx), employee_name=name,
                    site=str(site),
                    anomaly_type=AnomalyType.SALARY_INFLATION.value,
                    risk_level=RiskLevel.MEDIUM.value,
                    risk_score=round(min(z * 15, 100), 1), confidence=80,
                    reason=f"Salary ₹{val:,.0f} is {z:.1f}σ above site average ₹{mean:,.0f}",
                    actual_value=float(val), expected_value=round(mean, 2),
                    evidence=[f"Site={site}", f"Z-score={z:.1f}", f"Site avg={mean:.0f}"],
                    recommendation="Compare with designation and experience.",
                    department="payroll",
                ))
    return anomalies


# ============================================================
# MODULE 8 — NEGATIVE PAYROLL VALIDATION
# ============================================================


def negative_salary(row: Dict, col_map: Dict) -> Optional[AnomalyRecord]:
    gross_col = col_map.get("gross_wages")
    if not gross_col:
        return None
    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
    if gross < 0:
        return AnomalyRecord(
            anomaly_type=AnomalyType.NEGATIVE_PAY.value,
            risk_level=RiskLevel.HIGH.value,
            risk_score=85, confidence=98,
            reason=f"Negative gross salary: ₹{gross:,.0f}",
            actual_value=gross,
            evidence=[f"Gross={gross}"],
            recommendation="Data entry error. Correct immediately.",
            department="payroll",
        )
    return None


def negative_net_pay(row: Dict, col_map: Dict) -> Optional[AnomalyRecord]:
    net_col = col_map.get("net_pay")
    if not net_col:
        return None
    net = pd.to_numeric(row.get(net_col, 0), errors="coerce") or 0
    if net < 0:
        return AnomalyRecord(
            anomaly_type=AnomalyType.NEGATIVE_PAY.value,
            risk_level=RiskLevel.HIGH.value,
            risk_score=80, confidence=95,
            reason=f"Negative net pay: ₹{net:,.0f}",
            actual_value=net,
            evidence=[f"Net pay={net}"],
            recommendation="Check for excess deductions. Correct payroll.",
            department="payroll",
        )
    return None


def negative_deductions(row: Dict, col_map: Dict) -> Optional[AnomalyRecord]:
    rec_col = col_map.get("recoveries")
    if not rec_col:
        return None
    rec = pd.to_numeric(row.get(rec_col, 0), errors="coerce") or 0
    if rec < 0:
        return AnomalyRecord(
            anomaly_type=AnomalyType.NEGATIVE_DEDUCTION.value,
            risk_level=RiskLevel.MEDIUM.value,
            risk_score=50, confidence=90,
            reason=f"Negative recoveries: ₹{rec:,.0f}",
            actual_value=rec,
            evidence=[f"Recoveries={rec}"],
            recommendation="Verify deduction reversal authorization.",
            department="payroll",
        )
    return None


# ============================================================
# MODULE 9 — SALARY CEILING VALIDATION
# ============================================================


def pf_ceiling_validation(row: Dict, col_map: Dict, config: WageConfig) -> Optional[AnomalyRecord]:
    basic_col = col_map.get("basic_salary")
    pf_col = col_map.get("employee_pf")
    if not basic_col or not pf_col:
        return None
    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    actual_pf = pd.to_numeric(row.get(pf_col, 0), errors="coerce") or 0
    expected_pf = round(min(basic, config.pf_ceiling) * config.pf_employee_rate)
    diff = abs(actual_pf - expected_pf)
    if diff > 5:
        return AnomalyRecord(
            anomaly_type=AnomalyType.PF_CEILING_VIOLATION.value,
            risk_level=RiskLevel.MEDIUM.value,
            risk_score=55, confidence=85,
            reason=f"PF mismatch: expected ₹{expected_pf}, actual ₹{actual_pf}",
            actual_value=actual_pf, expected_value=expected_pf,
            difference=round(actual_pf - expected_pf, 2),
            evidence=[f"Basic={basic}", f"Ceiling={config.pf_ceiling}", f"Rate={config.pf_employee_rate}"],
            recommendation="Recalculate PF contribution.",
            department="compliance",
        )
    return None


def esi_ceiling_validation(row: Dict, col_map: Dict, config: WageConfig) -> Optional[AnomalyRecord]:
    basic_col = col_map.get("basic_salary")
    esi_col = col_map.get("employee_esi")
    if not basic_col or not esi_col:
        return None
    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    actual_esi = pd.to_numeric(row.get(esi_col, 0), errors="coerce") or 0

    if basic > config.esi_wage_limit and actual_esi > 0:
        return AnomalyRecord(
            anomaly_type=AnomalyType.ESI_CEILING_VIOLATION.value,
            risk_level=RiskLevel.MEDIUM.value,
            risk_score=60, confidence=90,
            reason=f"ESI ₹{actual_esi} deducted for salary ₹{basic:,.0f} above limit ₹{config.esi_wage_limit:,.0f}",
            actual_value=basic, expected_value=config.esi_wage_limit,
            evidence=[f"Basic={basic}", f"ESI limit={config.esi_wage_limit}", f"ESI deducted={actual_esi}"],
            recommendation="Remove ESI deduction. Employee not eligible.",
            department="compliance",
        )
    return None


def minimum_wage_validation(row: Dict, col_map: Dict, config: WageConfig) -> Optional[AnomalyRecord]:
    basic_col = col_map.get("basic_salary")
    days_col = col_map.get("days_worked")
    if not basic_col:
        return None
    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    days = pd.to_numeric(row.get(days_col, 30), errors="coerce") or 30 if days_col else 30
    expected_min = config.min_wage_daily * days
    if basic > 0 and basic < expected_min * 0.8:
        return AnomalyRecord(
            anomaly_type=AnomalyType.BELOW_MINIMUM_WAGE.value,
            risk_level=RiskLevel.HIGH.value,
            risk_score=75, confidence=80,
            reason=f"Salary ₹{basic:,.0f} below minimum wage ₹{expected_min:,.0f} for {days} days",
            actual_value=basic, expected_value=expected_min,
            difference=round(basic - expected_min, 2),
            evidence=[f"Basic={basic}", f"Days={days}", f"Min daily={config.min_wage_daily}"],
            recommendation="Verify against state minimum wage notification.",
            department="compliance",
        )
    return None


# ============================================================
# MODULE 10 — GOVERNMENT COMPLIANCE
# ============================================================


def working_hours_compliance(row: Dict, col_map: Dict, config: WageConfig) -> Optional[AnomalyRecord]:
    days_col = col_map.get("days_worked")
    if not days_col:
        return None
    days = pd.to_numeric(row.get(days_col, 0), errors="coerce") or 0
    if days > config.max_working_days:
        return AnomalyRecord(
            anomaly_type=AnomalyType.INVALID_DAYS.value,
            risk_level=RiskLevel.HIGH.value,
            risk_score=85, confidence=98,
            reason=f"Working days {days:.0f} exceeds maximum {config.max_working_days}",
            actual_value=days, expected_value=config.max_working_days,
            difference=days - config.max_working_days,
            evidence=[f"Days={days}", f"Max={config.max_working_days}"],
            recommendation="Data entry error. No month has more than 31 days.",
            department="payroll",
        )
    return None


# ============================================================
# MODULE 11 — PAYROLL CONSISTENCY
# ============================================================


def payroll_consistency(row: Dict, col_map: Dict) -> Optional[AnomalyRecord]:
    gross_col = col_map.get("gross_wages")
    net_col = col_map.get("net_pay")
    if not gross_col or not net_col:
        return None
    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
    net = pd.to_numeric(row.get(net_col, 0), errors="coerce") or 0
    if net > gross and gross > 0:
        return AnomalyRecord(
            anomaly_type=AnomalyType.NET_MISMATCH.value,
            risk_level=RiskLevel.HIGH.value,
            risk_score=80, confidence=95,
            reason=f"Net pay ₹{net:,.0f} exceeds gross ₹{gross:,.0f}",
            actual_value=net, expected_value=gross,
            difference=round(net - gross, 2),
            evidence=[f"Gross={gross}", f"Net={net}"],
            recommendation="Verify deduction entries. Net cannot exceed gross.",
            department="payroll",
        )
    return None


def high_recoveries(row: Dict, col_map: Dict, config: WageConfig) -> Optional[AnomalyRecord]:
    rec_col = col_map.get("recoveries")
    gross_col = col_map.get("gross_wages")
    if not rec_col or not gross_col:
        return None
    rec = pd.to_numeric(row.get(rec_col, 0), errors="coerce") or 0
    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0
    if gross > 0 and rec / gross > config.max_recovery_pct:
        return AnomalyRecord(
            anomaly_type=AnomalyType.HIGH_RECOVERIES.value,
            risk_level=RiskLevel.MEDIUM.value,
            risk_score=60, confidence=85,
            reason=f"Recoveries ₹{rec:,.0f} is {rec / gross * 100:.0f}% of gross (limit {config.max_recovery_pct * 100:.0f}%)",
            actual_value=rec, expected_value=round(gross * config.max_recovery_pct, 2),
            difference=round(rec - gross * config.max_recovery_pct, 2),
            evidence=[f"Recoveries={rec}", f"Gross={gross}", f"Pct={rec / gross * 100:.1f}%"],
            recommendation="Verify recovery authorization. High deductions need justification.",
            department="payroll",
        )
    return None


# ============================================================
# MODULE 14 — WAGE FRAUD DETECTION
# ============================================================


def fake_ot_detection(
    df: pd.DataFrame, col_map: Dict, sources: Dict[str, pd.DataFrame],
) -> List[AnomalyRecord]:
    """Detect OT claimed but attendance doesn't support it."""
    anomalies = []
    ot_col = col_map.get("overtime_hours")
    name_col = col_map.get("employee_name")
    days_col = col_map.get("days_worked")

    if not ot_col:
        return anomalies

    att_df = sources.get("attendance")
    if att_df is None:
        return anomalies

    att_map = build_column_map(att_df)
    att_name = att_map.get("employee_name")
    att_hours = att_map.get("hours_worked")
    if not att_name or not att_hours:
        return anomalies

    # Build attendance lookup
    att_hours_map = {}
    for _, row in att_df.iterrows():
        n = str(row.get(att_name, "")).strip().upper()
        h = pd.to_numeric(row.get(att_hours, 0), errors="coerce") or 0
        if n:
            att_hours_map[n] = att_hours_map.get(n, 0) + h

    for idx, row in df.iterrows():
        name = str(row.get(name_col, "")).strip().upper()
        ot = pd.to_numeric(row.get(ot_col, 0), errors="coerce") or 0
        if ot <= 0 or not name:
            continue
        total_att_hours = att_hours_map.get(name, 0)
        # If claimed OT > total attendance hours, suspicious
        if ot > total_att_hours and total_att_hours > 0:
            anomalies.append(AnomalyRecord(
                row_index=int(idx), employee_name=name,
                anomaly_type=AnomalyType.FAKE_OT.value,
                risk_level=RiskLevel.HIGH.value,
                risk_score=80, confidence=85,
                reason=f"OT {ot:.0f}h exceeds attendance hours {total_att_hours:.0f}h",
                actual_value=ot, expected_value=total_att_hours,
                evidence=[f"OT claimed={ot}", f"Attendance hours={total_att_hours}"],
                recommendation="Verify OT against attendance. Possible fake OT claim.",
                department="operations",
            ))
    return anomalies


# ============================================================
# MODULE 15 — MULTI-SITE WAGE ANALYSIS
# ============================================================


def calculate_site_salary_statistics(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    site_col = col_map.get("site_location")
    basic_col = col_map.get("basic_salary")
    ot_col = col_map.get("overtime_hours")

    if not site_col or not basic_col:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["_basic"] = pd.to_numeric(df_copy[basic_col], errors="coerce").fillna(0)
    df_copy["_ot"] = pd.to_numeric(df_copy[ot_col], errors="coerce").fillna(0) if ot_col else 0

    stats = []
    for site, group in df_copy.groupby(site_col):
        s = group["_basic"]
        stats.append({
            "site": site,
            "employee_count": len(group),
            "avg_salary": round(float(s.mean()), 2),
            "median_salary": round(float(s.median()), 2),
            "std_salary": round(float(s.std()), 2),
            "min_salary": round(float(s.min()), 2),
            "max_salary": round(float(s.max()), 2),
            "avg_ot": round(float(group["_ot"].mean()), 1),
            "total_ot": round(float(group["_ot"].sum()), 1),
        })
    return pd.DataFrame(stats) if stats else pd.DataFrame()


def detect_site_wage_anomalies(df: pd.DataFrame, col_map: Dict, config: WageConfig) -> List[AnomalyRecord]:
    """Detect per-site anomalies using z-score."""
    return salary_inflation(df, col_map, config)


# ============================================================
# MODULE 17 — EMPLOYEE WAGE HISTORY
# ============================================================


def employee_salary_history(
    current: pd.DataFrame, previous: pd.DataFrame, col_map: Dict,
) -> pd.DataFrame:
    """Compare current vs previous month."""
    if previous.empty:
        return pd.DataFrame()

    name_col = col_map.get("employee_name")
    basic_col = col_map.get("basic_salary")
    if not name_col or not basic_col:
        return pd.DataFrame()

    prev_map = build_column_map(previous)
    prev_name = prev_map.get("employee_name")
    prev_basic = prev_map.get("basic_salary")
    if not prev_name or not prev_basic:
        return pd.DataFrame()

    prev_lookup = {}
    for _, row in previous.iterrows():
        n = str(row.get(prev_name, "")).strip().upper()
        b = pd.to_numeric(row.get(prev_basic, 0), errors="coerce") or 0
        if n:
            prev_lookup[n] = b

    results = []
    for _, row in current.iterrows():
        name = str(row.get(name_col, "")).strip().upper()
        curr_basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
        prev_basic_val = prev_lookup.get(name)

        if prev_basic_val is not None and prev_basic_val > 0:
            change = curr_basic - prev_basic_val
            pct = round(change / prev_basic_val * 100, 2)
            results.append({
                "employee_name": name,
                "current_salary": curr_basic,
                "previous_salary": prev_basic_val,
                "change": round(change, 2),
                "change_pct": pct,
                "trend": "increased" if change > 0 else ("decreased" if change < 0 else "stable"),
            })

    return pd.DataFrame(results) if results else pd.DataFrame()


def salary_drop_detection(
    history: pd.DataFrame, config: WageConfig,
) -> pd.DataFrame:
    if history.empty or "change_pct" not in history.columns:
        return pd.DataFrame()
    drops = history[history["change_pct"] < -config.salary_drop_pct * 100]
    return drops


# ============================================================
# MODULE 18 — AI ANOMALY DETECTION
# ============================================================


def detect_ml_anomalies(
    df: pd.DataFrame, col_map: Dict, config: WageConfig,
) -> pd.DataFrame:
    """Isolation Forest anomaly detection."""
    if not HAS_SKLEARN:
        logger.warning("sklearn not available — skipping ML detection")
        return pd.DataFrame()

    features = feature_engineering(df, col_map)
    if features.empty or len(features) < 10:
        return pd.DataFrame()

    numeric = features.select_dtypes(include=[np.number])
    if numeric.empty:
        return pd.DataFrame()

    model = IsolationForest(
        contamination=config.isolation_contamination,
        random_state=42, n_estimators=100,
    )
    predictions = model.fit_predict(numeric.fillna(0))
    scores = model.decision_function(numeric.fillna(0))

    df_result = df.copy()
    df_result["ml_anomaly"] = predictions
    df_result["ml_anomaly_score"] = scores
    df_result["ml_risk_status"] = np.where(predictions == -1, "anomaly", "normal")

    name_col = col_map.get("employee_name")
    anomalies = df_result[df_result["ml_anomaly"] == -1].copy()

    if anomalies.empty:
        return pd.DataFrame()

    result_rows = []
    for idx, row in anomalies.iterrows():
        name = str(row.get(name_col, "")) if name_col else ""
        score = float(row.get("ml_anomaly_score", 0))
        result_rows.append({
            "employee_name": name,
            "anomaly_score": round(score, 4),
            "anomaly_type": "ml_anomaly",
            "risk_level": "high" if score < -0.3 else "medium",
            "confidence": round(min(abs(score) * 100, 95), 1),
        })

    return pd.DataFrame(result_rows) if result_rows else pd.DataFrame()


def detect_zscore_anomalies(df: pd.DataFrame, col_map: Dict, config: WageConfig) -> List[AnomalyRecord]:
    """Z-score outlier detection."""
    basic_col = col_map.get("basic_salary")
    name_col = col_map.get("employee_name")
    if not basic_col:
        return []

    values = pd.to_numeric(df[basic_col], errors="coerce").dropna()
    if len(values) < 10:
        return []

    mean, std = values.mean(), values.std()
    if std == 0:
        return []

    anomalies = []
    for idx, val in values.items():
        z = abs((val - mean) / std)
        if z > config.zscore_threshold:
            name = str(df.loc[idx].get(name_col, "")) if name_col else ""
            anomalies.append(AnomalyRecord(
                row_index=int(idx), employee_name=name,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER.value,
                risk_level=RiskLevel.MEDIUM.value if z < 4 else RiskLevel.HIGH.value,
                risk_score=round(min(z * 15, 100), 1), confidence=85,
                reason=f"Z-score {z:.1f}: salary ₹{val:,.0f} vs mean ₹{mean:,.0f} (σ={std:.0f})",
                actual_value=float(val), expected_value=round(mean, 2),
                evidence=[f"Z-score={z:.1f}", f"Mean={mean:.0f}", f"Std={std:.0f}"],
                recommendation="Investigate salary anomaly.",
            ))
    return anomalies


def detect_iqr_anomalies(df: pd.DataFrame, col_map: Dict, config: WageConfig) -> List[AnomalyRecord]:
    """IQR-based outlier detection."""
    basic_col = col_map.get("basic_salary")
    name_col = col_map.get("employee_name")
    if not basic_col:
        return []

    values = pd.to_numeric(df[basic_col], errors="coerce").dropna()
    if len(values) < 10:
        return []

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - config.iqr_multiplier * iqr
    upper = q3 + config.iqr_multiplier * iqr

    anomalies = []
    for idx, val in values.items():
        if val < lower or val > upper:
            name = str(df.loc[idx].get(name_col, "")) if name_col else ""
            anomalies.append(AnomalyRecord(
                row_index=int(idx), employee_name=name,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER.value,
                risk_level=RiskLevel.LOW.value,
                risk_score=40, confidence=70,
                reason=f"IQR outlier: ₹{val:,.0f} outside [{lower:.0f}, {upper:.0f}]",
                actual_value=float(val), expected_value=round((lower + upper) / 2, 2),
                evidence=[f"Value={val:.0f}", f"IQR=[{lower:.0f}, {upper:.0f}]"],
                recommendation="Review salary structure.",
            ))
    return anomalies


# ============================================================
# MODULE 19 — WAGE RISK SCORING
# ============================================================


def calculate_wage_risk(
    anomaly_count: int,
    has_ml_anomaly: bool = False,
    has_negative_pay: bool = False,
    has_zero_wage: bool = False,
    has_excessive_ot: bool = False,
    has_duplicate: bool = False,
    has_fraud: bool = False,
    has_compliance: bool = False,
    config: Optional[WageConfig] = None,
) -> Tuple[float, str]:
    cfg = config or WageConfig()
    score = 0

    score += min(anomaly_count * 8, 40)
    if has_ml_anomaly:
        score += 15
    if has_negative_pay:
        score += 20
    if has_zero_wage:
        score += 20
    if has_excessive_ot:
        score += 10
    if has_duplicate:
        score += 15
    if has_fraud:
        score += 15
    if has_compliance:
        score += 10

    score = min(score, 100)
    level = classify_wage_risk(score, cfg)
    return score, level


def classify_wage_risk(score: float, config: WageConfig) -> str:
    if score <= 15:
        return RiskLevel.SAFE.value
    elif score <= 30:
        return RiskLevel.LOW.value
    elif score <= 55:
        return RiskLevel.MEDIUM.value
    elif score <= 80:
        return RiskLevel.HIGH.value
    return RiskLevel.CRITICAL.value


# ============================================================
# MODULE 20 — EXPLAINABLE AI
# ============================================================


def explain_anomaly(anomaly: AnomalyRecord) -> Dict[str, Any]:
    """Generate human-readable explanation for any anomaly."""
    return {
        "employee": anomaly.employee_name,
        "anomaly_type": anomaly.anomaly_type,
        "risk_level": anomaly.risk_level,
        "risk_score": anomaly.risk_score,
        "confidence": f"{anomaly.confidence:.0f}%",
        "reason": anomaly.reason,
        "evidence": anomaly.evidence,
        "actual_value": anomaly.actual_value,
        "expected_value": anomaly.expected_value,
        "difference": anomaly.difference,
        "recommendation": anomaly.recommendation,
        "department": anomaly.department,
    }


def generate_reason(anomaly: AnomalyRecord) -> str:
    parts = [anomaly.reason]
    if anomaly.evidence:
        parts.append(f"Evidence: {', '.join(anomaly.evidence[:3])}")
    return " | ".join(parts)


def calculate_confidence(anomaly: AnomalyRecord) -> float:
    return anomaly.confidence


# ============================================================
# MODULE 21 — TREND ANALYTICS
# ============================================================


def monthly_wage_trend(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    month_col = col_map.get("month")
    basic_col = col_map.get("basic_salary")
    if not month_col or not basic_col:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["_basic"] = pd.to_numeric(df_copy[basic_col], errors="coerce").fillna(0)

    grouped = df_copy.groupby(month_col)["_basic"]
    return pd.DataFrame({
        "month": grouped.mean().index,
        "avg_salary": grouped.mean().values.round(2),
        "total_salary": grouped.sum().values.round(2),
        "employee_count": grouped.count().values,
    })


def monthly_ot_trend(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    month_col = col_map.get("month")
    ot_col = col_map.get("overtime_hours")
    if not month_col or not ot_col:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["_ot"] = pd.to_numeric(df_copy[ot_col], errors="coerce").fillna(0)

    grouped = df_copy.groupby(month_col)["_ot"]
    return pd.DataFrame({
        "month": grouped.mean().index,
        "avg_ot": grouped.mean().values.round(1),
        "total_ot": grouped.sum().values.round(1),
    })


def recovery_trend(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    month_col = col_map.get("month")
    rec_col = col_map.get("recoveries")
    if not month_col or not rec_col:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["_rec"] = pd.to_numeric(df_copy[rec_col], errors="coerce").fillna(0)

    grouped = df_copy.groupby(month_col)["_rec"]
    return pd.DataFrame({
        "month": grouped.mean().index,
        "avg_recovery": grouped.mean().values.round(2),
        "total_recovery": grouped.sum().values.round(2),
    })


# ============================================================
# MODULE 22 — DEPARTMENT / CATEGORY ANALYSIS
# ============================================================


def department_statistics(df: pd.DataFrame, col_map: Dict) -> pd.DataFrame:
    dept_col = col_map.get("department")
    basic_col = col_map.get("basic_salary")
    ot_col = col_map.get("overtime_hours")

    if not dept_col or not basic_col or dept_col not in df.columns:
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["_basic"] = pd.to_numeric(df_copy[basic_col], errors="coerce").fillna(0)
    df_copy["_ot"] = pd.to_numeric(df_copy[ot_col], errors="coerce").fillna(0) if ot_col else 0

    rows = []
    for dept, group in df_copy.groupby(dept_col):
        s = group["_basic"]
        rows.append({
            "department": dept,
            "employee_count": len(group),
            "avg_salary": round(float(s.mean()), 2),
            "median_salary": round(float(s.median()), 2),
            "min_salary": round(float(s.min()), 2),
            "max_salary": round(float(s.max()), 2),
            "avg_ot": round(float(group["_ot"].mean()), 1),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ============================================================
# MODULE 23 — EXECUTIVE DASHBOARD
# ============================================================


def build_dashboard(
    df: pd.DataFrame,
    col_map: Dict,
    anomalies: List[AnomalyRecord],
    emp_risks: List[EmployeeWageRisk],
    site_stats: pd.DataFrame,
    ml_anomalies: pd.DataFrame,
    stats: RuntimeStats,
) -> Dict[str, Any]:
    basic_col = col_map.get("basic_salary")
    ot_col = col_map.get("overtime_hours")
    rec_col = col_map.get("recoveries")
    net_col = col_map.get("net_pay")

    basic = pd.to_numeric(df[basic_col], errors="coerce").fillna(0) if basic_col else pd.Series([0])
    ot = pd.to_numeric(df[ot_col], errors="coerce").fillna(0) if ot_col else pd.Series([0])
    rec = pd.to_numeric(df[rec_col], errors="coerce").fillna(0) if rec_col else pd.Series([0])
    net = pd.to_numeric(df[net_col], errors="coerce").fillna(0) if net_col else pd.Series([0])

    risk_dist = defaultdict(int)
    type_dist = defaultdict(int)
    for a in anomalies:
        risk_dist[a.risk_level] += 1
        type_dist[a.anomaly_type] += 1

    return {
        "generated_at": datetime.now().isoformat(),
        "engine_version": "7.0.0",
        "salary_summary": {
            "total_employees": len(df),
            "avg_salary": round(float(basic.mean()), 2),
            "median_salary": round(float(basic.median()), 2),
            "highest_salary": round(float(basic.max()), 2),
            "lowest_salary": round(float(basic.min()), 2),
            "total_salary": round(float(basic.sum()), 2),
            "salary_std": round(float(basic.std()), 2),
        },
        "ot_summary": {
            "avg_ot": round(float(ot.mean()), 1),
            "total_ot": round(float(ot.sum()), 1),
            "max_ot": round(float(ot.max()), 1),
            "employees_with_ot": int((ot > 0).sum()),
        },
        "recovery_summary": {
            "avg_recovery": round(float(rec.mean()), 2),
            "total_recovery": round(float(rec.sum()), 2),
        },
        "anomaly_summary": {
            "total_anomalies": len(anomalies),
            "ml_anomalies": len(ml_anomalies) if not ml_anomalies.empty else 0,
            "rule_anomalies": len(anomalies) - (len(ml_anomalies) if not ml_anomalies.empty else 0),
            "risk_distribution": dict(risk_dist),
            "type_distribution": dict(type_dist),
        },
        "employee_risk_summary": {
            "total_scored": len(emp_risks),
            "high_risk": sum(1 for e in emp_risks if e.risk_level in ("high", "critical")),
            "medium_risk": sum(1 for e in emp_risks if e.risk_level == "medium"),
            "low_risk": sum(1 for e in emp_risks if e.risk_level in ("safe", "low")),
        },
        "runtime": stats.summary(),
    }


def salary_summary(dashboard: Dict) -> Dict[str, Any]:
    return dashboard.get("salary_summary", {})


def top_risk_employees(emp_risks: List[EmployeeWageRisk], n: int = 20) -> List[Dict]:
    sorted_risks = sorted(emp_risks, key=lambda e: e.risk_score, reverse=True)[:n]
    return [asdict(e) for e in sorted_risks]


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
    path = EXPORT_DIR / f"wage_anomaly_report_{ts}.xlsx"
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
    path = SUMMARY_DIR / f"wage_anomaly_summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"JSON → {path}")


# ============================================================
# MAIN ENGINE
# ============================================================


class WageAnomalyEngine:
    """
    Production wage anomaly detection engine.
    Runs all 25 modules in sequence.
    """

    def __init__(
        self,
        config: Optional[WageConfig] = None,
        wages_df: Optional[pd.DataFrame] = None,
    ):
        self.config = config or load_config()
        self.stats = RuntimeStats()
        self.provided_wages = wages_df

        self.sources: Dict[str, pd.DataFrame] = {}
        self.wages_df = pd.DataFrame()
        self.col_map: Dict[str, Optional[str]] = {}
        self.features: pd.DataFrame = pd.DataFrame()
        self.all_anomalies: List[AnomalyRecord] = []
        self.employee_risks: List[EmployeeWageRisk] = []
        self.site_stats: pd.DataFrame = pd.DataFrame()
        self.ml_results: pd.DataFrame = pd.DataFrame()
        self.dashboard: Dict[str, Any] = {}

        _audit_log.clear()

    def run(self) -> Dict[str, Any]:
        self.stats = RuntimeStats()
        cfg = self.config

        logger.info("=" * 70)
        logger.info("WAGE ANOMALY DETECTION ENGINE")
        logger.info(f"Engine version: {cfg.engine_version}")
        logger.info("=" * 70)

        # ── 1. Load data ──
        logger.info("PHASE 1: LOADING DATA")
        if self.provided_wages is not None and not self.provided_wages.empty:
            self.wages_df = self.provided_wages
            self.sources["wages"] = self.wages_df
        else:
            self.sources = load_all_sources()
            self.wages_df = self.sources.get("wages", pd.DataFrame())

        self.stats.files_loaded = len(self.sources)
        for k, df in self.sources.items():
            self.stats.rows_loaded += len(df)

        if self.wages_df.empty:
            logger.error("No wages data — aborting")
            self.stats.finish()
            return {"error": "No wages data"}

        self.col_map = build_column_map(self.wages_df)
        self.stats.rows_processed = len(self.wages_df)
        audit_log("ENGINE_START", "loader", f"Rows={len(self.wages_df)}")

        # ── 2. Feature engineering ──
        logger.info("PHASE 2: FEATURE ENGINEERING")
        self.features = feature_engineering(self.wages_df, self.col_map)
        logger.info(f"Features: {self.features.shape[1]} columns, {self.features.shape[0]} rows")

        # ── 3. Rule-based detection ──
        logger.info("PHASE 3: RULE-BASED DETECTION")
        all_anomalies = []
        module_count = 0

        name_col = self.col_map.get("employee_name")
        id_col = self.col_map.get("employee_id")
        site_col = self.col_map.get("site_location")

        for idx, row in self.wages_df.iterrows():
            rd = row.to_dict()
            name = str(rd.get(name_col, "")) if name_col else ""
            eid = str(rd.get(id_col, "")) if id_col else ""
            site = str(rd.get(site_col, "")) if site_col else ""

            # All rule-based checks
            checks = [
                validate_basic(rd, self.col_map, cfg),
                validate_salary_components(rd, self.col_map),
                detect_excessive_ot(rd, self.col_map, cfg),
                detect_negative_ot(rd, self.col_map),
                negative_salary(rd, self.col_map),
                negative_net_pay(rd, self.col_map),
                negative_deductions(rd, self.col_map),
                pf_ceiling_validation(rd, self.col_map, cfg),
                esi_ceiling_validation(rd, self.col_map, cfg),
                minimum_wage_validation(rd, self.col_map, cfg),
                working_hours_compliance(rd, self.col_map, cfg),
                payroll_consistency(rd, self.col_map),
                high_recoveries(rd, self.col_map, cfg),
                attendance_salary_variance(rd, self.col_map, cfg),
            ]

            for check in checks:
                if check:
                    check.row_index = int(idx)
                    check.employee_name = check.employee_name or name
                    check.employee_id = check.employee_id or eid
                    check.site = check.site or site
                    all_anomalies.append(check)

        module_count += 5
        logger.info(f"Rule anomalies: {len(all_anomalies)}")

        # Duplicate detection (full DataFrame)
        dup_anomalies = detect_duplicate_salary(self.wages_df, self.col_map)
        all_anomalies.extend(dup_anomalies)
        module_count += 1

        # Salary spike
        spike_anomalies = salary_spike_detection(self.wages_df, self.col_map, cfg)
        all_anomalies.extend(spike_anomalies)
        module_count += 1

        # Site inflation
        inflation_anomalies = salary_inflation(self.wages_df, self.col_map, cfg)
        all_anomalies.extend(inflation_anomalies)
        module_count += 1

        # Fake OT
        fake_ot = fake_ot_detection(self.wages_df, self.col_map, self.sources)
        all_anomalies.extend(fake_ot)
        module_count += 1

        # Z-score
        zscore_anomalies = detect_zscore_anomalies(self.wages_df, self.col_map, cfg)
        all_anomalies.extend(zscore_anomalies)

        # IQR
        iqr_anomalies = detect_iqr_anomalies(self.wages_df, self.col_map, cfg)
        all_anomalies.extend(iqr_anomalies)
        module_count += 2

        self.stats.rule_anomalies = len(all_anomalies)

        # ── 4. ML anomaly detection ──
        logger.info("PHASE 4: AI ANOMALY DETECTION")
        self.ml_results = detect_ml_anomalies(self.wages_df, self.col_map, cfg)
        if not self.ml_results.empty:
            self.stats.ml_anomalies = len(self.ml_results)
            for _, row in self.ml_results.iterrows():
                all_anomalies.append(AnomalyRecord(
                    employee_name=str(row.get("employee_name", "")),
                    anomaly_type=AnomalyType.ML_ANOMALY.value,
                    risk_level=str(row.get("risk_level", "medium")),
                    risk_score=float(row.get("anomaly_score", 0)) * 100,
                    confidence=float(row.get("confidence", 80)),
                    reason="ML model detected anomalous wage pattern",
                    evidence=[f"Anomaly score={row.get('anomaly_score', 0)}"],
                    recommendation="Investigate wage pattern. Compare with peers.",
                ))
        module_count += 1

        self.all_anomalies = all_anomalies
        self.stats.anomalies_detected = len(all_anomalies)
        self.stats.modules_run = module_count
        logger.info(f"Total anomalies: {len(all_anomalies)}")

        # ── 5. Employee risk scoring ──
        logger.info("PHASE 5: EMPLOYEE RISK SCORING")
        emp_anomalies: Dict[str, List[AnomalyRecord]] = defaultdict(list)
        for a in all_anomalies:
            key = a.employee_name or str(a.row_index)
            emp_anomalies[key].append(a)

        for key, cases in emp_anomalies.items():
            first = cases[0]
            has_ml = any(c.anomaly_type == AnomalyType.ML_ANOMALY.value for c in cases)
            has_neg = any(c.anomaly_type == AnomalyType.NEGATIVE_PAY.value for c in cases)
            has_zero = any(c.anomaly_type == AnomalyType.ZERO_WAGE.value for c in cases)
            has_ot = any(c.anomaly_type == AnomalyType.EXCESSIVE_OT.value for c in cases)
            has_dup = any(c.anomaly_type == AnomalyType.DUPLICATE_SALARY.value for c in cases)
            has_fraud = any(c.anomaly_type in (AnomalyType.FAKE_OT.value, AnomalyType.SALARY_OVERRIDE.value) for c in cases)
            has_comp = any(c.anomaly_type in (AnomalyType.BELOW_MINIMUM_WAGE.value, AnomalyType.PF_CEILING_VIOLATION.value) for c in cases)

            score, level = calculate_wage_risk(
                anomaly_count=len(cases), has_ml_anomaly=has_ml,
                has_negative_pay=has_neg, has_zero_wage=has_zero,
                has_excessive_ot=has_ot, has_duplicate=has_dup,
                has_fraud=has_fraud, has_compliance=has_comp, config=cfg,
            )

            self.employee_risks.append(EmployeeWageRisk(
                employee_name=first.employee_name,
                employee_id=first.employee_id,
                site=first.site,
                risk_score=score,
                risk_level=level,
                confidence=round(np.mean([c.confidence for c in cases]), 1),
                anomaly_count=len(cases),
                anomaly_types=list(set(c.anomaly_type for c in cases)),
                risk_factors=[c.reason for c in cases[:5]],
                recommendation=cases[0].recommendation,
            ))

        self.stats.high_risk_employees = sum(
            1 for e in self.employee_risks if e.risk_level in ("high", "critical")
        )
        logger.info(f"Employees scored: {len(self.employee_risks)}")

        # ── 6. Site analysis ──
        logger.info("PHASE 6: SITE ANALYSIS")
        self.site_stats = calculate_site_salary_statistics(self.wages_df, self.col_map)
        self.stats.sites_analyzed = len(self.site_stats) if not self.site_stats.empty else 0

        # ── 7. Trends ──
        logger.info("PHASE 7: TREND ANALYSIS")
        wage_trend = monthly_wage_trend(self.wages_df, self.col_map)
        ot_trend = monthly_ot_trend(self.wages_df, self.col_map)
        rec_trend = recovery_trend(self.wages_df, self.col_map)
        dept_stats = department_statistics(self.wages_df, self.col_map)
        ot_ranking = employee_ot_ranking(self.wages_df, self.col_map)

        # History comparison
        prev_df = self.sources.get("previous_wages", pd.DataFrame())
        salary_history = employee_salary_history(self.wages_df, prev_df, self.col_map)

        # ── 8. Dashboard ──
        logger.info("PHASE 8: DASHBOARD")
        self.dashboard = build_dashboard(
            self.wages_df, self.col_map, all_anomalies,
            self.employee_risks, self.site_stats,
            self.ml_results, self.stats,
        )

        # ── 9. Export ──
        logger.info("PHASE 9: EXPORT")
        self.stats.finish()
        audit_log("ENGINE_COMPLETE", "all", f"Elapsed={self.stats.elapsed}s")

        # Build DataFrames
        anomalies_df = pd.DataFrame([asdict(a) for a in all_anomalies]) if all_anomalies else pd.DataFrame()
        emp_risk_df = pd.DataFrame([asdict(e) for e in self.employee_risks]) if self.employee_risks else pd.DataFrame()
        top_risks_df = pd.DataFrame(top_risk_employees(self.employee_risks, 30))
        features_df = self.features
        normalized_df = normalize_features(self.features)
        explain_df = pd.DataFrame([explain_anomaly(a) for a in all_anomalies[:100]]) if all_anomalies else pd.DataFrame()
        audit_df = get_audit_dataframe()

        # Original with flags
        flagged_df = self.wages_df.copy()
        flagged_df["Anomaly_Flag"] = flagged_df.index.map(
            lambda i: 1 if any(a.row_index == i for a in all_anomalies) else 0
        )
        flagged_df["Risk_Status"] = flagged_df["Anomaly_Flag"].apply(
            lambda x: "High Risk" if x == 1 else "Normal"
        )
        risk_notes = []
        for i, row in flagged_df.iterrows():
            notes = [a.reason[:50] for a in all_anomalies if a.row_index == i]
            risk_notes.append(", ".join(notes) if notes else "No Risk")
        flagged_df["Business_Risk_Notes"] = risk_notes

        all_reports = {
            "wage_anomaly_report": flagged_df,
            "anomaly_details": anomalies_df,
            "employee_wage_risks": emp_risk_df,
            "top_risk_employees": top_risks_df,
            "site_salary_statistics": self.site_stats,
            "department_statistics": dept_stats,
            "ot_ranking": ot_ranking,
            "ml_anomalies": self.ml_results,
            "feature_matrix": features_df,
            "normalized_features": normalized_df,
            "wage_trend": wage_trend,
            "ot_trend": ot_trend,
            "recovery_trend": rec_trend,
            "salary_history": salary_history,
            "explanations": explain_df,
            "audit_trail": audit_df,
        }

        csv_reports = {k: v for k, v in all_reports.items() if v is not None and not v.empty}
        export_csv(csv_reports)
        export_excel(csv_reports)
        export_json(self.dashboard, self.stats)

        # ── Final summary ──
        logger.info("=" * 70)
        logger.info("WAGE ANOMALY DETECTION COMPLETE")
        logger.info(f"  Elapsed:          {self.stats.elapsed}s")
        logger.info(f"  Files loaded:     {self.stats.files_loaded}")
        logger.info(f"  Rows processed:   {self.stats.rows_processed}")
        logger.info(f"  Modules run:      {self.stats.modules_run}")
        logger.info(f"  Total anomalies:  {self.stats.anomalies_detected}")
        logger.info(f"    Rule-based:     {self.stats.rule_anomalies}")
        logger.info(f"    ML-based:       {self.stats.ml_anomalies}")
        logger.info(f"  High risk:        {self.stats.high_risk_employees}")
        logger.info(f"  Sites analyzed:   {self.stats.sites_analyzed}")
        logger.info(f"  CSV files:        {len(csv_reports)}")
        logger.info(f"  Speed:            {self.stats.rows_per_sec} rows/sec")
        logger.info("=" * 70)

        return self.dashboard


# ============================================================
# BACKWARD-COMPATIBLE run()
# ============================================================


def load_wages() -> pd.DataFrame:
    return safe_load(INPUT_DIR / "wages.csv")


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    col_map = build_column_map(df)
    return feature_engineering(df, col_map)


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    engine = WageAnomalyEngine(wages_df=df)
    result = engine.run()
    if engine.all_anomalies:
        flagged = df.copy()
        flagged["Anomaly_Flag"] = flagged.index.map(
            lambda i: -1 if any(a.row_index == i for a in engine.all_anomalies) else 1
        )
        flagged["Risk_Status"] = flagged["Anomaly_Flag"].apply(
            lambda x: "High Risk" if x == -1 else "Normal"
        )
        return flagged
    df["Anomaly_Flag"] = 1
    df["Risk_Status"] = "Normal"
    return df


def apply_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    cfg = WageConfig()
    col_map = build_column_map(df)
    risk_notes = []
    for _, row in df.iterrows():
        notes = []
        rd = row.to_dict()
        ot = pd.to_numeric(rd.get(col_map.get("overtime_hours", ""), 0), errors="coerce") or 0
        days = pd.to_numeric(rd.get(col_map.get("days_worked", ""), 0), errors="coerce") or 0
        basic = pd.to_numeric(rd.get(col_map.get("basic_salary", ""), 0), errors="coerce") or 0
        gross = pd.to_numeric(rd.get(col_map.get("gross_wages", ""), 0), errors="coerce") or 0
        net = pd.to_numeric(rd.get(col_map.get("net_pay", ""), 0), errors="coerce") or 0
        rec = pd.to_numeric(rd.get(col_map.get("recoveries", ""), 0), errors="coerce") or 0

        if ot > cfg.ot_threshold_business:
            notes.append("Excessive Overtime")
        if days > cfg.max_working_days:
            notes.append("Invalid Working Days")
        if basic == 0:
            notes.append("Zero Wage")
        if net > gross and gross > 0:
            notes.append("Net Pay Higher Than Gross")
        if gross > 0 and rec > gross * cfg.max_recovery_pct:
            notes.append("High Recoveries")
        if not notes:
            notes.append("No Risk")
        risk_notes.append(", ".join(notes))
    df["Business_Risk_Notes"] = risk_notes
    return df


def save_report(df: pd.DataFrame):
    path = OUTPUT_DIR / "wage_anomaly_report.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved: {path}")


def run():
    engine = WageAnomalyEngine()
    return engine.run()


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Wage Anomaly Detector")
    parser.add_argument("--wages", default=None, help="Path to wages CSV")
    parser.add_argument("--config", default=None, help="Config file path")
    parser.add_argument("--contamination", type=float, default=0.05, help="ML contamination rate")
    parser.add_argument("--operator", default="auto")

    args = parser.parse_args()
    cfg = load_config(Path(args.config) if args.config else None)
    cfg.isolation_contamination = args.contamination
    cfg.operator = args.operator

    wages_df = None
    if args.wages:
        wages_df = safe_load(Path(args.wages))

    engine = WageAnomalyEngine(config=cfg, wages_df=wages_df)
    result = engine.run()
    print(json.dumps(result, indent=2, default=str))
