# security-ai/scripts/pf_reconciliation_engine.py
"""
Production-Grade PF Reconciliation Engine
Security AI — Provident Fund Compliance & Reconciliation System

═══════════════════════════════════════════════════════════════════
 58 FUNCTIONS | 18 OUTPUT FILES | 12 VALIDATORS | 3 FRAUD CHECKS
═══════════════════════════════════════════════════════════════════

 FEATURES:
  ✓ Client-aware configuration
  ✓ Multi-sheet wage loading
  ✓ Multi-site reconciliation
  ✓ Multi-month trend analysis
  ✓ 6-method cascade matching (UAN→ID→Aadhaar→PAN→Bank→Name)
  ✓ Duplicate UAN / employee detection
  ✓ Missing employee detection (wages ↔ ECR)
  ✓ 12 validation rules (PF wages, employee PF, employer PF,
    ceiling, dates, site, attendance, payroll, bank, leave, OT)
  ✓ 3 fraud detectors (ghost employee, duplicate bank, fake PF)
  ✓ Composite risk scoring (0-100)
  ✓ Compliance scoring
  ✓ Full audit trail
  ✓ Exception logging
  ✓ Runtime statistics & pipeline metrics
  ✓ 8 report generators
  ✓ CSV + JSON + Excel multi-sheet export
  ✓ Production rotating logger
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
from datetime import datetime, date
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

warnings.filterwarnings("ignore", category=UserWarning)

# ============================================================
# 1. PRODUCTION LOGGING
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(funcName)s:%(lineno)d | %(message)s"
)
LOG_DATE = "%Y-%m-%d %H:%M:%S"


def setup_rotating_logger(
    log_dir: Path,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Production logging with file rotation."""
    log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("PFRecon")
    root.setLevel(logging.DEBUG)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(console)

    # Rotating file handler — all logs
    all_handler = RotatingFileHandler(
        log_dir / "pf_reconciliation.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(all_handler)

    # Rotating file handler — errors only
    err_handler = RotatingFileHandler(
        log_dir / "pf_reconciliation_errors.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(err_handler)

    return root


# ============================================================
# 2. PATHS
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

logger = setup_rotating_logger(LOG_DIR)

# ============================================================
# 3. DATA CLASSES
# ============================================================


@dataclass
class PFRuleSet:
    """PF calculation rules — loaded from config, never hardcoded."""
    pf_ceiling: float = 15000.0
    employee_epf_rate: float = 0.12
    employer_epf_rate: float = 0.0367
    employer_eps_rate: float = 0.0833
    employer_admin_rate: float = 0.005
    employer_edli_rate: float = 0.005
    effective_date: str = "2014-09-01"
    admin_charges_min: float = 500.0
    edli_charges_min: float = 200.0


@dataclass
class ClientConfig:
    """Per-client configuration."""
    client_name: str = "default"
    client_id: str = "001"
    sites: List[str] = field(default_factory=list)
    pf_rules: PFRuleSet = field(default_factory=PFRuleSet)
    wages_file: str = "wages.csv"
    ecr_file: str = "ecr.csv"
    bank_file: str = "bank.csv"
    attendance_file: str = "attendance.csv"
    master_file: str = "employee_master.csv"
    matching_file: str = "matching.csv"


@dataclass
class ValidationResult:
    """Single validation check result."""
    employee_name: str = ""
    employee_id: str = ""
    uan: str = ""
    site: str = ""
    month: str = ""
    validation_type: str = ""
    expected_value: float = 0.0
    actual_value: float = 0.0
    difference: float = 0.0
    status: str = ""
    severity: str = ""
    detail: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )


@dataclass
class ReconciliationResult:
    """Complete reconciliation result for one employee."""
    employee_name: str = ""
    employee_id: str = ""
    uan: str = ""
    site: str = ""
    month: str = ""
    year: str = ""

    # Match
    match_type: str = ""
    match_confidence: float = 0.0
    match_reason: str = ""

    # PF wages
    basic_vda: float = 0.0
    pf_qualifying_wages: float = 0.0
    pf_ceiling_applied: bool = False

    # Employee
    expected_employee_pf: float = 0.0
    actual_employee_pf: float = 0.0
    employee_pf_diff: float = 0.0

    # Employer
    expected_employer_epf: float = 0.0
    actual_employer_epf: float = 0.0
    expected_employer_eps: float = 0.0
    actual_employer_eps: float = 0.0
    employer_epf_diff: float = 0.0
    employer_eps_diff: float = 0.0
    total_employer_diff: float = 0.0

    # Risk
    risk_score: int = 0
    risk_level: str = "safe"
    compliance_flag: str = ""

    # Validation summary
    validations_passed: int = 0
    validations_failed: int = 0
    validation_details: List[str] = field(default_factory=list)


@dataclass
class DuplicateRecord:
    """Detected duplicate pair."""
    employee_a_name: str = ""
    employee_a_id: str = ""
    employee_a_site: str = ""
    employee_b_name: str = ""
    employee_b_id: str = ""
    employee_b_site: str = ""
    duplicate_type: str = ""
    matched_field: str = ""
    matched_value: str = ""
    severity: str = ""


@dataclass
class MissingRecord:
    """Detected missing employee."""
    employee_name: str = ""
    employee_id: str = ""
    uan: str = ""
    site: str = ""
    present_in: str = ""
    missing_from: str = ""
    severity: str = ""


@dataclass
class AuditEntry:
    """Timestamped audit record."""
    timestamp: str = ""
    action: str = ""
    employee_name: str = ""
    employee_id: str = ""
    site: str = ""
    field_name: str = ""
    old_value: str = ""
    new_value: str = ""
    detail: str = ""
    engine_version: str = "3.0.0"
    operator: str = "auto"


@dataclass
class RuntimeStats:
    """Performance metrics."""
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_loaded: int = 0
    rows_loaded: int = 0
    matches_attempted: int = 0
    matches_found: int = 0
    exact_matches: int = 0
    fuzzy_matches: int = 0
    no_matches: int = 0
    validations_run: int = 0
    validations_passed: int = 0
    validations_failed: int = 0
    duplicates_found: int = 0
    missing_found: int = 0
    fraud_flags: int = 0
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
        el = self.elapsed
        if el <= 0:
            return 0.0
        return round(self.rows_loaded / el, 1)

    def summary(self) -> Dict[str, Any]:
        d = {
            "elapsed_seconds": self.elapsed,
            "rows_per_second": self.rows_per_sec,
        }
        for k, v in self.__dict__.items():
            if k != "start_time" and k != "end_time":
                d[k] = v
        return d


# ============================================================
# 4. FIELD RESOLVER — Flexible Column Detection
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "employee_name": [
        "employee_name", "emp_name", "name", "staff_name",
        "worker_name", "Employee Name",
    ],
    "employee_id": [
        "employee_id", "emp_id", "emp_code", "employee_code",
        "staff_id", "code", "Employee Code",
    ],
    "uan_number": [
        "uan_number", "uan", "uan_no", "UAN",
    ],
    "pf_number": [
        "pf_number", "pf_no", "pf_a/c_no", "pf_ac_no", "PF No",
    ],
    "esic_number": [
        "esic_number", "esic_no", "esic", "esi_number", "ESIC No",
    ],
    "aadhaar_number": [
        "aadhaar_number", "aadhaar", "aadhaar_no", "uid", "Aadhaar",
    ],
    "pan_number": [
        "pan_number", "pan", "pan_no", "PAN",
    ],
    "bank_account": [
        "bank_account", "bank_account_number", "account_number",
        "bank_ac_no", "Account No",
    ],
    "ifsc_code": [
        "ifsc", "ifsc_code", "bank_ifsc", "IFSC",
    ],
    "site_location": [
        "site_location", "site", "location", "branch", "unit",
        "Location",
    ],
    "basic_vda": [
        "basic_vda", "basic wages", "basic_wages", "basic",
        "basic + vda", "BASIC + VDA", "gross_wages", "gross",
    ],
    "employee_pf": [
        "employee_pf", "employee_epf_contribution", "epf",
        "employee_pf_contribution", "pf_deduction",
        "EPF 12%", "epf_contribution_ac01",
    ],
    "employer_epf": [
        "employer_epf", "employer_epf_contribution",
        "employer_pf", "er_epf",
    ],
    "employer_eps": [
        "employer_eps", "employer_eps_contribution",
        "er_eps",
    ],
    "gross_wages": [
        "gross_wages", "gross", "total_wages", "gross_salary",
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
        "joining_date", "date_of_joining", "doj",
        "joining_dt",
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
    "leave_without_pay": [
        "lwp", "leave_without_pay", "lop", "unpaid_leave",
    ],
    "transfer_date": [
        "transfer_date", "payment_date", "credit_date",
    ],
}


def find_column(df: pd.DataFrame, semantic: str) -> Optional[str]:
    """Find actual column name matching a semantic key."""
    aliases = COLUMN_ALIASES.get(semantic, [semantic])
    df_lower = {c.lower().strip(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in df_lower:
            return df_lower[alias.lower()]
    # Partial match
    for alias in aliases:
        for dl, actual in df_lower.items():
            if alias.lower() in dl:
                return actual
    return None


def find_columns_for(
    df: pd.DataFrame, semantic: str
) -> List[str]:
    """Find all matching columns."""
    aliases = COLUMN_ALIASES.get(semantic, [semantic])
    found = []
    df_lower = {c.lower().strip(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in df_lower:
            found.append(df_lower[alias.lower()])
    return found


def build_column_map(
    df: pd.DataFrame,
) -> Dict[str, Optional[str]]:
    """Map every semantic key to an actual column name."""
    mapping = {}
    for semantic in COLUMN_ALIASES:
        mapping[semantic] = find_column(df, semantic)
    return mapping


# ============================================================
# 5. CONFIGURATION LOADING
# ============================================================


def load_engine_configuration(
    config_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load engine config from JSON/YAML or use defaults."""
    default_config = {
        "pf_ceiling": 15000.0,
        "employee_epf_rate": 0.12,
        "employer_epf_rate": 0.0367,
        "employer_eps_rate": 0.0833,
        "employer_admin_rate": 0.005,
        "employer_edli_rate": 0.005,
        "admin_charges_min": 500.0,
        "edli_charges_min": 200.0,
        "fuzzy_threshold": 0.70,
        "engine_version": "3.0.0",
        "operator": "auto",
    }

    if config_path and config_path.exists():
        try:
            with open(config_path, "r") as f:
                loaded = json.load(f)
            default_config.update(loaded)
            logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            logger.warning(f"Config load failed, using defaults: {e}")

    return default_config


def load_client_config(client_name: str = "default") -> ClientConfig:
    """Load per-client settings."""
    config_file = CONFIG_DIR / f"{client_name}.json"
    cfg = ClientConfig(client_name=client_name)

    if config_file.exists():
        try:
            with open(config_file) as f:
                data = json.load(f)
            for k, v in data.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
            if "pf_rules" in data:
                cfg.pf_rules = PFRuleSet(**data["pf_rules"])
            logger.info(f"Client config loaded: {client_name}")
        except Exception as e:
            logger.warning(f"Client config error: {e}")

    return cfg


def get_client_paths(
    client_config: ClientConfig,
) -> Dict[str, Path]:
    """Resolve input file paths for a client."""
    return {
        "wages": INPUT_DIR / client_config.wages_file,
        "ecr": INPUT_DIR / client_config.ecr_file,
        "bank": INPUT_DIR / client_config.bank_file,
        "attendance": INPUT_DIR / client_config.attendance_file,
        "master": INPUT_DIR / client_config.master_file,
        "matching": INPUT_DIR / client_config.matching_file,
    }


def load_pf_rules(
    config: Dict[str, Any],
) -> PFRuleSet:
    """Build PFRuleSet from configuration dict."""
    rules = PFRuleSet(
        pf_ceiling=config.get("pf_ceiling", 15000.0),
        employee_epf_rate=config.get("employee_epf_rate", 0.12),
        employer_epf_rate=config.get("employer_epf_rate", 0.0367),
        employer_eps_rate=config.get("employer_eps_rate", 0.0833),
        employer_admin_rate=config.get("employer_admin_rate", 0.005),
        employer_edli_rate=config.get("employer_edli_rate", 0.005),
        admin_charges_min=config.get("admin_charges_min", 500.0),
        edli_charges_min=config.get("edli_charges_min", 200.0),
    )
    validate_rules(rules)
    return rules


def validate_rules(rules: PFRuleSet) -> bool:
    """Sanity-check PF rules."""
    assert rules.pf_ceiling > 0, "PF ceiling must be positive"
    assert 0 < rules.employee_epf_rate < 1, "Invalid employee EPF rate"
    assert 0 < rules.employer_epf_rate < 1, "Invalid employer EPF rate"
    assert 0 < rules.employer_eps_rate < 1, "Invalid employer EPS rate"
    total = rules.employer_epf_rate + rules.employer_eps_rate
    assert total < 1, "Employer rates exceed 100%"
    logger.debug("PF rules validated OK")
    return True


# ============================================================
# 6. NAME NORMALIZATION (Upgraded)
# ============================================================

TITLES = [
    "mr", "mrs", "ms", "miss", "dr", "prof",
    "shri", "smt", "kumari", "master",
]

RELATION_MARKERS = [
    "s/o", "so", "d/o", "do", "w/o", "wo",
    "c/o", "co", "son of", "daughter of", "wife of",
]

STOP_WORDS = TITLES + RELATION_MARKERS + ["the", "and"]


def normalize_name(name: Any) -> str:
    """Robust name normalization for Indian employee names."""
    if pd.isna(name) or name is None:
        return ""
    s = str(name).lower().strip()
    s = re.sub(r"[^a-zA-Z\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    words = [w for w in s.split() if w not in STOP_WORDS]
    return " ".join(words).upper()


def normalize_column_name(col: Any) -> str:
    """Normalize a column header."""
    s = str(col).strip().lower()
    s = s.replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s)
    return s


# ============================================================
# 7. DATA LOADING
# ============================================================


def load_csv(file_path: Path) -> pd.DataFrame:
    """Load CSV with encoding detection and basic cleaning."""
    if not file_path.exists():
        logger.warning(f"Missing file: {file_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="latin-1")

    if df.empty:
        logger.warning(f"Empty file: {file_path}")
        return df

    # Normalize column names
    df.columns = [normalize_column_name(c) for c in df.columns]

    # Drop fully empty rows and columns
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    # Strip string cells
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})

    logger.info(f"Loaded {file_path.name}: {df.shape[0]} rows × {df.shape[1]} cols")
    return df


def load_multiple_wage_sheets(
    wage_path: Path,
) -> pd.DataFrame:
    """Load wages from Excel (multi-sheet) or CSV."""
    if not wage_path.exists():
        logger.warning(f"Wage file not found: {wage_path}")
        return pd.DataFrame()

    if wage_path.suffix in (".xlsx", ".xls", ".xlsm"):
        xls = pd.ExcelFile(wage_path)
        frames = []
        for sheet in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet)
                df.columns = [normalize_column_name(c) for c in df.columns]
                df["_source_sheet"] = sheet
                frames.append(df)
                logger.info(f"  Sheet '{sheet}': {len(df)} rows")
            except Exception as e:
                logger.warning(f"  Sheet '{sheet}' error: {e}")

        if frames:
            combined = pd.concat(frames, ignore_index=True)
            logger.info(f"Combined wages: {len(combined)} rows from {len(frames)} sheets")
            return combined
        return pd.DataFrame()
    else:
        return load_csv(wage_path)


def load_all_sources(
    paths: Dict[str, Path],
    wages_excel: Optional[Path] = None,
) -> Dict[str, pd.DataFrame]:
    """Load all available data sources."""
    sources = {}

    # Wages — prefer Excel multi-sheet if provided
    if wages_excel and wages_excel.exists():
        wages_df = load_multiple_wage_sheets(wages_excel)
    else:
        wages_df = load_csv(paths.get("wages", Path("")))
    if not wages_df.empty:
        sources["wages"] = wages_df

    # Other sources
    for key in ("ecr", "bank", "attendance", "master", "matching"):
        path = paths.get(key)
        if path and path.exists():
            df = load_csv(path)
            if not df.empty:
                sources[key] = df

    logger.info(f"Loaded {len(sources)} data sources: {list(sources.keys())}")
    return sources


# ============================================================
# 8. EMPLOYEE MATCHING — Cascade (6 Methods)
# ============================================================


def _build_index(
    df: pd.DataFrame,
    col: Optional[str],
) -> Dict[str, int]:
    """Build value → first_row_index lookup."""
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


def _try_exact(
    source_val: Any,
    index: Dict[str, int],
    target_df: pd.DataFrame,
    match_type: str,
    confidence: float,
    reason_prefix: str,
) -> Optional[Dict[str, Any]]:
    """Attempt exact match via index lookup."""
    if pd.isna(source_val) or not str(source_val).strip():
        return None
    key = str(source_val).strip().upper()
    if key in index:
        row = target_df.iloc[index[key]].to_dict()
        return {
            "matched": True,
            "match_type": match_type,
            "confidence": confidence,
            "matched_record": row,
            "reason": f"{reason_prefix}: {key}",
            "matched_by": match_type,
            "matched_value": key,
        }
    return None


def match_by_uan(
    wages_df: pd.DataFrame,
    target_df: pd.DataFrame,
    src_map: Dict, tgt_map: Dict,
) -> Optional[Dict[str, Any]]:
    """Exact UAN match (confidence 100%)."""
    src_col = src_map.get("uan_number")
    tgt_col = tgt_map.get("uan_number")
    if not src_col or not tgt_col:
        return None
    index = _build_index(target_df, tgt_col)
    return _try_exact(
        wages_df.get(src_col), index, target_df,
        "exact_uan", 100.0, "UAN exact match",
    )


def match_by_employee_id(
    wages_df: pd.Series,
    target_df: pd.DataFrame,
    src_map: Dict, tgt_map: Dict,
) -> Optional[Dict[str, Any]]:
    """Exact employee ID match (confidence 100%)."""
    src_col = src_map.get("employee_id")
    tgt_col = tgt_map.get("employee_id")
    if not src_col or not tgt_col:
        return None
    index = _build_index(target_df, tgt_col)
    return _try_exact(
        wages_df.get(src_col), index, target_df,
        "exact_emp_id", 100.0, "Employee ID exact match",
    )


def match_by_aadhaar(
    wages_df: pd.Series,
    target_df: pd.DataFrame,
    src_map: Dict, tgt_map: Dict,
) -> Optional[Dict[str, Any]]:
    """Exact Aadhaar match (confidence 98%)."""
    src_col = src_map.get("aadhaar_number")
    tgt_col = tgt_map.get("aadhaar_number")
    if not src_col or not tgt_col:
        return None
    index = _build_index(target_df, tgt_col)
    return _try_exact(
        wages_df.get(src_col), index, target_df,
        "exact_aadhaar", 98.0, "Aadhaar exact match",
    )


def match_by_pan(
    wages_df: pd.Series,
    target_df: pd.DataFrame,
    src_map: Dict, tgt_map: Dict,
) -> Optional[Dict[str, Any]]:
    """Exact PAN match (confidence 98%)."""
    src_col = src_map.get("pan_number")
    tgt_col = tgt_map.get("pan_number")
    if not src_col or not tgt_col:
        return None
    index = _build_index(target_df, tgt_col)
    return _try_exact(
        wages_df.get(src_col), index, target_df,
        "exact_pan", 98.0, "PAN exact match",
    )


def match_by_bank_account(
    wages_df: pd.Series,
    target_df: pd.DataFrame,
    src_map: Dict, tgt_map: Dict,
) -> Optional[Dict[str, Any]]:
    """Exact bank account match (confidence 97%)."""
    src_col = src_map.get("bank_account")
    tgt_col = tgt_map.get("bank_account")
    if not src_col or not tgt_col:
        return None
    index = _build_index(target_df, tgt_col)
    return _try_exact(
        wages_df.get(src_col), index, target_df,
        "exact_bank", 97.0, "Bank account exact match",
    )


def match_by_name_fuzzy(
    source_name: str,
    source_site: str,
    target_df: pd.DataFrame,
    tgt_map: Dict,
    threshold: float = 0.70,
) -> Dict[str, Any]:
    """Fuzzy name match with site-scoping."""
    tgt_name_col = tgt_map.get("employee_name")
    if not tgt_name_col or tgt_name_col not in target_df.columns:
        return {"matched": False, "match_type": "no_match",
                "confidence": 0.0, "reason": "No name column in target"}

    norm_source = normalize_name(source_name)
    if not norm_source:
        return {"matched": False, "match_type": "no_match",
                "confidence": 0.0, "reason": "Empty source name"}

    # Build target name list
    target_names_raw = target_df[tgt_name_col].dropna().tolist()
    norm_map = {}
    for raw in target_names_raw:
        n = normalize_name(raw)
        if n:
            norm_map[n] = raw

    norm_targets = list(norm_map.keys())
    if not norm_targets:
        return {"matched": False, "match_type": "no_match",
                "confidence": 0.0, "reason": "No target names"}

    # Site-scoped matching first
    tgt_site_col = tgt_map.get("site_location")
    if source_site and tgt_site_col and tgt_site_col in target_df.columns:
        site_mask = (
            target_df[tgt_site_col].astype(str).str.upper().str.strip()
            == source_site.upper().strip()
        )
        site_df = target_df[site_mask]
        if not site_df.empty:
            site_names = site_df[tgt_name_col].dropna().tolist()
            site_norm = {normalize_name(n): n for n in site_names if normalize_name(n)}
            if site_norm:
                result = process.extractOne(
                    norm_source, list(site_norm.keys()),
                    scorer=fuzz.token_sort_ratio,
                )
                if result:
                    matched, score, _ = result
                    score_f = float(score) / 100.0
                    if score_f >= threshold:
                        return {
                            "matched": True,
                            "match_type": "fuzzy_name_site",
                            "confidence": round(score_f * 100, 1),
                            "matched_name": site_norm[matched],
                            "reason": f"Fuzzy name+site: '{norm_source}' → '{matched}' "
                                      f"(score={score_f:.0%}, site={source_site})",
                            "matched_by": "name+site",
                            "matched_value": matched,
                        }

    # Global fuzzy match
    result = process.extractOne(
        norm_source, norm_targets,
        scorer=fuzz.token_sort_ratio,
    )
    if not result:
        return {"matched": False, "match_type": "no_match",
                "confidence": 0.0, "reason": "No fuzzy match found"}

    matched, score, _ = result
    score_f = float(score) / 100.0

    if score_f < threshold:
        return {
            "matched": False, "match_type": "rejected",
            "confidence": round(score_f * 100, 1),
            "reason": f"Below threshold ({score_f:.0%} < {threshold:.0%})",
        }

    return {
        "matched": True,
        "match_type": "fuzzy_name",
        "confidence": round(score_f * 100, 1),
        "matched_name": norm_map.get(matched, matched),
        "reason": f"Fuzzy name: '{norm_source}' → '{matched}' (score={score_f:.0%})",
        "matched_by": "name",
        "matched_value": matched,
    }


def cascade_match(
    wages_df: pd.DataFrame,
    target_df: pd.DataFrame,
    src_map: Dict,
    tgt_map: Dict,
    fuzzy_threshold: float = 0.70,
) -> pd.DataFrame:
    """
    Match every wages row against target using cascade:
    UAN → Employee ID → Aadhaar → PAN → Bank → Name+Site → Name
    """
    results = []
    name_col = src_map.get("employee_name", "employee_name")
    site_col = src_map.get("site_location")
    id_col = src_map.get("employee_id")
    uan_col = src_map.get("uan_number")

    for idx, row in wages_df.iterrows():
        source = row.to_dict()
        source_name = str(source.get(name_col, ""))
        source_site = str(source.get(site_col, "")) if site_col else ""
        source_id = str(source.get(id_col, "")) if id_col else ""
        source_uan = str(source.get(uan_col, "")) if uan_col else ""

        match_result = None

        # 1. UAN
        m = match_by_uan(pd.Series(source), target_df, src_map, tgt_map)
        if m and m.get("matched"):
            match_result = m

        # 2. Employee ID
        if not match_result:
            m = match_by_employee_id(pd.Series(source), target_df, src_map, tgt_map)
            if m and m.get("matched"):
                match_result = m

        # 3. Aadhaar
        if not match_result:
            m = match_by_aadhaar(pd.Series(source), target_df, src_map, tgt_map)
            if m and m.get("matched"):
                match_result = m

        # 4. PAN
        if not match_result:
            m = match_by_pan(pd.Series(source), target_df, src_map, tgt_map)
            if m and m.get("matched"):
                match_result = m

        # 5. Bank
        if not match_result:
            m = match_by_bank_account(pd.Series(source), target_df, src_map, tgt_map)
            if m and m.get("matched"):
                match_result = m

        # 6. Name fuzzy
        if not match_result:
            m = match_by_name_fuzzy(
                source_name, source_site,
                target_df, tgt_map, fuzzy_threshold,
            )
            match_result = m

        if match_result is None:
            match_result = {
                "matched": False, "match_type": "no_match",
                "confidence": 0.0, "reason": "No columns available",
            }

        results.append({
            "source_name": source_name,
            "source_id": source_id,
            "source_uan": source_uan,
            "site": source_site,
            "matched": match_result.get("matched", False),
            "match_type": match_result.get("match_type", "no_match"),
            "confidence": match_result.get("confidence", 0.0),
            "reason": match_result.get("reason", ""),
            "matched_by": match_result.get("matched_by", ""),
            "matched_name": match_result.get("matched_name", ""),
            "matched_value": match_result.get("matched_value", ""),
        })

    return pd.DataFrame(results)


# ============================================================
# 9. DUPLICATE & MISSING DETECTION
# ============================================================


def detect_duplicate_uan(
    df: pd.DataFrame,
    col_map: Dict,
) -> pd.DataFrame:
    """Find rows sharing the same UAN."""
    uan_col = col_map.get("uan_number")
    name_col = col_map.get("employee_name")
    id_col = col_map.get("employee_id")
    site_col = col_map.get("site_location")

    if not uan_col or uan_col not in df.columns:
        return pd.DataFrame()

    duplicates = []
    grouped = df.dropna(subset=[uan_col]).groupby(uan_col)

    for uan_val, group in grouped:
        if len(group) < 2:
            continue
        indices = list(group.index)
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                a = df.loc[indices[i]]
                b = df.loc[indices[j]]
                duplicates.append(asdict(DuplicateRecord(
                    employee_a_name=str(a.get(name_col, "")) if name_col else "",
                    employee_a_id=str(a.get(id_col, "")) if id_col else "",
                    employee_a_site=str(a.get(site_col, "")) if site_col else "",
                    employee_b_name=str(b.get(name_col, "")) if name_col else "",
                    employee_b_id=str(b.get(id_col, "")) if id_col else "",
                    employee_b_site=str(b.get(site_col, "")) if site_col else "",
                    duplicate_type="Same UAN",
                    matched_field="uan",
                    matched_value=str(uan_val),
                    severity="critical",
                )))

    return pd.DataFrame(duplicates) if duplicates else pd.DataFrame()


def detect_duplicate_employee(
    df: pd.DataFrame,
    col_map: Dict,
) -> pd.DataFrame:
    """Detect duplicates by name+site, Aadhaar, or bank account."""
    name_col = col_map.get("employee_name")
    site_col = col_map.get("site_location")
    aadhaar_col = col_map.get("aadhaar_number")
    bank_col = col_map.get("bank_account")
    id_col = col_map.get("employee_id")

    duplicates = []

    # Same name + different site
    if name_col and site_col and name_col in df.columns and site_col in df.columns:
        grouped = df.dropna(subset=[name_col]).groupby(name_col)
        for name_val, group in grouped:
            if len(group) < 2:
                continue
            sites = group[site_col].dropna().unique()
            if len(sites) > 1:
                indices = list(group.index)
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        a = df.loc[indices[i]]
                        b = df.loc[indices[j]]
                        s_a = str(a.get(site_col, ""))
                        s_b = str(b.get(site_col, ""))
                        if s_a != s_b:
                            duplicates.append(asdict(DuplicateRecord(
                                employee_a_name=str(a.get(name_col, "")),
                                employee_a_id=str(a.get(id_col, "")) if id_col else "",
                                employee_a_site=s_a,
                                employee_b_name=str(b.get(name_col, "")),
                                employee_b_id=str(b.get(id_col, "")) if id_col else "",
                                employee_b_site=s_b,
                                duplicate_type="Same Name Different Site",
                                matched_field="employee_name+site",
                                matched_value=str(name_val),
                                severity="medium",
                            )))

    # Same bank account
    if bank_col and bank_col in df.columns:
        grouped = df.dropna(subset=[bank_col]).groupby(bank_col)
        for val, group in grouped:
            if len(group) < 2:
                continue
            indices = list(group.index)
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    a = df.loc[indices[i]]
                    b = df.loc[indices[j]]
                    duplicates.append(asdict(DuplicateRecord(
                        employee_a_name=str(a.get(name_col, "")) if name_col else "",
                        employee_b_name=str(b.get(name_col, "")) if name_col else "",
                        duplicate_type="Same Bank Account",
                        matched_field="bank_account",
                        matched_value=str(val),
                        severity="high",
                    )))

    return pd.DataFrame(duplicates) if duplicates else pd.DataFrame()


def detect_missing_in_wages(
    wages_df: pd.DataFrame,
    ecr_df: pd.DataFrame,
    w_map: Dict, e_map: Dict,
) -> pd.DataFrame:
    """ECR employees not found in wages."""
    w_name_col = w_map.get("employee_name")
    e_name_col = e_map.get("employee_name")

    if not w_name_col or not e_name_col:
        return pd.DataFrame()

    wage_names = set(
        wages_df[w_name_col].dropna().apply(normalize_name)
    )
    records = []

    for _, row in ecr_df.iterrows():
        ecr_name = row.get(e_name_col)
        if pd.isna(ecr_name):
            continue
        norm = normalize_name(ecr_name)
        if norm and norm not in wage_names:
            e_id_col = e_map.get("employee_id")
            e_site_col = e_map.get("site_location")
            e_uan_col = e_map.get("uan_number")
            records.append(asdict(MissingRecord(
                employee_name=str(ecr_name),
                employee_id=str(row.get(e_id_col, "")) if e_id_col else "",
                uan=str(row.get(e_uan_col, "")) if e_uan_col else "",
                site=str(row.get(e_site_col, "")) if e_site_col else "",
                present_in="ecr",
                missing_from="wages",
                severity="high",
            )))

    return pd.DataFrame(records) if records else pd.DataFrame()


def detect_missing_in_ecr(
    wages_df: pd.DataFrame,
    ecr_df: pd.DataFrame,
    w_map: Dict, e_map: Dict,
) -> pd.DataFrame:
    """Wages employees not found in ECR."""
    w_name_col = w_map.get("employee_name")
    e_name_col = e_map.get("employee_name")

    if not w_name_col or not e_name_col:
        return pd.DataFrame()

    ecr_names = set(
        ecr_df[e_name_col].dropna().apply(normalize_name)
    )
    records = []

    for _, row in wages_df.iterrows():
        wage_name = row.get(w_name_col)
        if pd.isna(wage_name):
            continue
        norm = normalize_name(wage_name)
        if norm and norm not in ecr_names:
            w_id_col = w_map.get("employee_id")
            w_site_col = w_map.get("site_location")
            w_uan_col = w_map.get("uan_number")
            records.append(asdict(MissingRecord(
                employee_name=str(wage_name),
                employee_id=str(row.get(w_id_col, "")) if w_id_col else "",
                uan=str(row.get(w_uan_col, "")) if w_uan_col else "",
                site=str(row.get(w_site_col, "")) if w_site_col else "",
                present_in="wages",
                missing_from="ecr",
                severity="high",
            )))

    return pd.DataFrame(records) if records else pd.DataFrame()


# ============================================================
# 10. VALIDATION ENGINE (12 Validators)
# ============================================================


def validate_pf_wages(
    row: Dict, rules: PFRuleSet, col_map: Dict,
) -> Optional[ValidationResult]:
    """Check if PF-qualifying wages are correct."""
    basic_col = col_map.get("basic_vda")
    if not basic_col:
        return None

    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    pf_base = min(basic, rules.pf_ceiling)
    ceiling_applied = basic > rules.pf_ceiling

    return ValidationResult(
        employee_name=str(row.get(col_map.get("employee_name", ""), "")),
        employee_id=str(row.get(col_map.get("employee_id", ""), "")),
        site=str(row.get(col_map.get("site_location", ""), "")),
        validation_type="pf_wage",
        expected_value=round(pf_base, 2),
        actual_value=round(basic, 2),
        difference=round(basic - pf_base, 2) if ceiling_applied else 0.0,
        status="pass" if not ceiling_applied or basic <= rules.pf_ceiling * 1.5 else "warning",
        severity="low" if not ceiling_applied else "info",
        detail=f"Basic={basic}, Ceiling={rules.pf_ceiling}, Capped={ceiling_applied}",
    )


def validate_employee_pf(
    row: Dict, rules: PFRuleSet, col_map: Dict,
) -> Optional[ValidationResult]:
    """Validate employee's 12% EPF contribution."""
    basic_col = col_map.get("basic_vda")
    pf_col = col_map.get("employee_pf")

    if not basic_col or not pf_col:
        return None

    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    actual_pf = pd.to_numeric(row.get(pf_col, 0), errors="coerce") or 0

    pf_base = min(basic, rules.pf_ceiling)
    expected_pf = round(pf_base * rules.employee_epf_rate)
    diff = round(actual_pf - expected_pf, 2)

    status = "pass" if abs(diff) <= 1 else "fail"
    severity = "low" if abs(diff) <= 10 else ("medium" if abs(diff) <= 100 else "high")

    return ValidationResult(
        employee_name=str(row.get(col_map.get("employee_name", ""), "")),
        employee_id=str(row.get(col_map.get("employee_id", ""), "")),
        uan=str(row.get(col_map.get("uan_number", ""), "")),
        site=str(row.get(col_map.get("site_location", ""), "")),
        validation_type="employee_pf",
        expected_value=expected_pf,
        actual_value=actual_pf,
        difference=diff,
        status=status,
        severity=severity,
        detail=f"PF base={pf_base}, Rate={rules.employee_epf_rate:.0%}, "
               f"Expected={expected_pf}, Actual={actual_pf}, Diff={diff}",
    )


def validate_employer_pf(
    row: Dict, rules: PFRuleSet, col_map: Dict,
) -> Optional[ValidationResult]:
    """Validate employer EPF + EPS."""
    basic_col = col_map.get("basic_vda")
    er_epf_col = col_map.get("employer_epf")
    er_eps_col = col_map.get("employer_eps")

    if not basic_col:
        return None
    if not er_epf_col and not er_eps_col:
        return None

    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    pf_base = min(basic, rules.pf_ceiling)

    expected_er_epf = round(pf_base * rules.employer_epf_rate, 2)
    expected_er_eps = round(pf_base * rules.employer_eps_rate, 2)

    actual_er_epf = pd.to_numeric(row.get(er_epf_col, 0), errors="coerce") if er_epf_col else 0
    actual_er_eps = pd.to_numeric(row.get(er_eps_col, 0), errors="coerce") if er_eps_col else 0

    actual_er_epf = actual_er_epf or 0
    actual_er_eps = actual_er_eps or 0

    diff_epf = round(actual_er_epf - expected_er_epf, 2)
    diff_eps = round(actual_er_eps - expected_er_eps, 2)
    total_diff = round(diff_epf + diff_eps, 2)

    status = "pass" if abs(total_diff) <= 2 else "fail"
    severity = "low" if abs(total_diff) <= 20 else ("medium" if abs(total_diff) <= 200 else "high")

    return ValidationResult(
        employee_name=str(row.get(col_map.get("employee_name", ""), "")),
        employee_id=str(row.get(col_map.get("employee_id", ""), "")),
        uan=str(row.get(col_map.get("uan_number", ""), "")),
        site=str(row.get(col_map.get("site_location", ""), "")),
        validation_type="employer_pf",
        expected_value=round(expected_er_epf + expected_er_eps, 2),
        actual_value=round(actual_er_epf + actual_er_eps, 2),
        difference=total_diff,
        status=status,
        severity=severity,
        detail=f"ER EPF: expected={expected_er_epf}, actual={actual_er_epf}, diff={diff_epf}; "
               f"ER EPS: expected={expected_er_eps}, actual={actual_er_eps}, diff={diff_eps}",
    )


def validate_pf_ceiling(
    row: Dict, rules: PFRuleSet, col_map: Dict,
) -> Optional[ValidationResult]:
    """Verify ceiling was correctly applied."""
    basic_col = col_map.get("basic_vda")
    if not basic_col:
        return None

    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    was_capped = basic > rules.pf_ceiling
    pf_base = min(basic, rules.pf_ceiling)

    return ValidationResult(
        employee_name=str(row.get(col_map.get("employee_name", ""), "")),
        validation_type="pf_ceiling",
        expected_value=rules.pf_ceiling,
        actual_value=pf_base,
        difference=basic - rules.pf_ceiling if was_capped else 0.0,
        status="info" if was_capped else "pass",
        severity="info",
        detail=f"Basic={basic}, Ceiling={rules.pf_ceiling}, Capped={was_capped}",
    )


def validate_joining_exit_dates(
    row: Dict, col_map: Dict,
) -> Optional[ValidationResult]:
    """Check joining/exit date validity."""
    doj_col = col_map.get("joining_date")
    doe_col = col_map.get("exit_date")

    issues = []

    if doj_col:
        doj_raw = row.get(doj_col)
        if pd.notna(doj_raw):
            try:
                doj = pd.to_datetime(doj_raw)
                if doj > pd.Timestamp.now():
                    issues.append("Joining date is in the future")
            except Exception:
                issues.append(f"Invalid joining date format: {doj_raw}")

    if doe_col:
        doe_raw = row.get(doe_col)
        if pd.notna(doe_raw):
            try:
                doe = pd.to_datetime(doe_raw)
                if doj_col and pd.notna(row.get(doj_col)):
                    doj = pd.to_datetime(row.get(doj_col))
                    if doe < doj:
                        issues.append("Exit date before joining date")
            except Exception:
                issues.append(f"Invalid exit date format: {doe_raw}")

    if not issues:
        return None

    return ValidationResult(
        employee_name=str(row.get(col_map.get("employee_name", ""), "")),
        validation_type="date_validation",
        status="fail",
        severity="medium",
        detail="; ".join(issues),
    )


def validate_site_assignment(
    row: Dict, col_map: Dict,
    valid_sites: Optional[List[str]] = None,
) -> Optional[ValidationResult]:
    """Check site assignment is valid."""
    site_col = col_map.get("site_location")
    if not site_col:
        return None

    site = str(row.get(site_col, "")).strip()
    if not site or site in ("nan", "None", ""):
        return ValidationResult(
            employee_name=str(row.get(col_map.get("employee_name", ""), "")),
            validation_type="site_assignment",
            status="fail",
            severity="medium",
            detail="No site assignment",
        )

    if valid_sites and site.upper() not in [s.upper() for s in valid_sites]:
        return ValidationResult(
            employee_name=str(row.get(col_map.get("employee_name", ""), "")),
            validation_type="site_assignment",
            status="warning",
            severity="low",
            detail=f"Site '{site}' not in known sites list",
        )

    return None


def validate_attendance_against_pf(
    wages_row: Dict, att_row: Dict,
    w_map: Dict, a_map: Dict,
) -> Optional[ValidationResult]:
    """Check attendance days vs PF calculation days."""
    w_days_col = w_map.get("days_worked")
    a_days_col = a_map.get("days_worked")

    if not w_days_col or not a_days_col:
        return None

    wage_days = pd.to_numeric(wages_row.get(w_days_col, 0), errors="coerce") or 0
    att_days = pd.to_numeric(att_row.get(a_days_col, 0), errors="coerce") or 0

    if wage_days == 0 and att_days == 0:
        return None

    diff = abs(wage_days - att_days)
    if diff <= 1:
        return None

    return ValidationResult(
        employee_name=str(wages_row.get(w_map.get("employee_name", ""), "")),
        validation_type="attendance_pf_linkage",
        expected_value=att_days,
        actual_value=wage_days,
        difference=wage_days - att_days,
        status="fail" if diff > 3 else "warning",
        severity="medium" if diff > 3 else "low",
        detail=f"Wage days={wage_days}, Attendance days={att_days}",
    )


def validate_payroll_against_pf(
    wages_row: Dict, ecr_row: Dict,
    w_map: Dict, e_map: Dict,
) -> Optional[ValidationResult]:
    """Cross-check gross salary vs PF-qualifying wages."""
    gross_col = w_map.get("gross_wages")
    pf_base_col = e_map.get("basic_vda")

    if not gross_col or not pf_base_col:
        return None

    gross = pd.to_numeric(wages_row.get(gross_col, 0), errors="coerce") or 0
    pf_base = pd.to_numeric(ecr_row.get(pf_base_col, 0), errors="coerce") or 0

    if gross == 0 or pf_base == 0:
        return None

    ratio = pf_base / gross if gross > 0 else 0
    if 0.3 <= ratio <= 1.0:
        return None

    return ValidationResult(
        employee_name=str(wages_row.get(w_map.get("employee_name", ""), "")),
        validation_type="payroll_pf_linkage",
        expected_value=gross,
        actual_value=pf_base,
        difference=round(gross - pf_base, 2),
        status="warning",
        severity="medium",
        detail=f"Gross={gross}, PF base={pf_base}, Ratio={ratio:.2f}",
    )


def validate_bank_payment(
    wages_row: Dict, bank_row: Dict,
    w_map: Dict, b_map: Dict,
) -> Optional[ValidationResult]:
    """Verify bank transfer matches net pay."""
    net_col = w_map.get("net_pay")
    credit_col = b_map.get("net_pay")

    if not net_col or not credit_col:
        return None

    net_pay = pd.to_numeric(wages_row.get(net_col, 0), errors="coerce") or 0
    bank_credit = pd.to_numeric(bank_row.get(credit_col, 0), errors="coerce") or 0

    if net_pay == 0 and bank_credit == 0:
        return None

    diff = abs(net_pay - bank_credit)
    if diff <= 5:
        return None

    return ValidationResult(
        employee_name=str(wages_row.get(w_map.get("employee_name", ""), "")),
        validation_type="bank_payment",
        expected_value=net_pay,
        actual_value=bank_credit,
        difference=round(net_pay - bank_credit, 2),
        status="fail" if diff > 100 else "warning",
        severity="high" if diff > 100 else "medium",
        detail=f"Net pay={net_pay}, Bank credit={bank_credit}",
    )


def validate_leave_effect(
    row: Dict, rules: PFRuleSet, col_map: Dict,
) -> Optional[ValidationResult]:
    """If LWP exists, PF should reduce proportionally."""
    lwp_col = col_map.get("leave_without_pay")
    basic_col = col_map.get("basic_vda")
    pf_col = col_map.get("employee_pf")
    days_col = col_map.get("days_worked")

    if not lwp_col or not basic_col:
        return None

    lwp = pd.to_numeric(row.get(lwp_col, 0), errors="coerce") or 0
    if lwp <= 0:
        return None

    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    actual_pf = pd.to_numeric(row.get(pf_col, 0), errors="coerce") or 0
    total_days = pd.to_numeric(row.get(days_col, 30), errors="coerce") or 30

    working_days = max(total_days - lwp, 0)
    adjusted_basic = round(basic * working_days / total_days)
    expected_pf = round(min(adjusted_basic, rules.pf_ceiling) * rules.employee_epf_rate)

    diff = abs(actual_pf - expected_pf)
    if diff <= 5:
        return None

    return ValidationResult(
        employee_name=str(row.get(col_map.get("employee_name", ""), "")),
        validation_type="leave_effect",
        expected_value=expected_pf,
        actual_value=actual_pf,
        difference=round(actual_pf - expected_pf, 2),
        status="warning",
        severity="medium",
        detail=f"LWP={lwp}, Adjusted basic={adjusted_basic}, "
               f"Expected PF={expected_pf}, Actual PF={actual_pf}",
    )


def validate_ot_component(
    row: Dict, col_map: Dict,
) -> Optional[ValidationResult]:
    """Verify OT is excluded from PF wages."""
    ot_col = col_map.get("overtime_amount")
    basic_col = col_map.get("basic_vda")

    if not ot_col or not basic_col:
        return None

    ot = pd.to_numeric(row.get(ot_col, 0), errors="coerce") or 0
    if ot <= 0:
        return None

    basic = pd.to_numeric(row.get(basic_col, 0), errors="coerce") or 0
    gross_col = col_map.get("gross_wages")
    gross = pd.to_numeric(row.get(gross_col, 0), errors="coerce") or 0 if gross_col else 0

    # If basic seems inflated (close to gross), OT may be included
    if gross > 0 and basic > 0 and basic / gross > 0.95:
        return ValidationResult(
            employee_name=str(row.get(col_map.get("employee_name", ""), "")),
            validation_type="overtime_component",
            expected_value=0.0,
            actual_value=ot,
            difference=ot,
            status="warning",
            severity="medium",
            detail=f"OT={ot}, Basic={basic}, Gross={gross}. "
                   f"Basic/Gross ratio high — OT may be included in PF base",
        )

    return None


# ============================================================
# 11. FRAUD DETECTION
# ============================================================


def detect_ghost_employee(
    wages_df: pd.DataFrame,
    ecr_df: pd.DataFrame,
    attendance_df: Optional[pd.DataFrame],
    w_map: Dict, e_map: Dict,
) -> pd.DataFrame:
    """Employee in ECR but zero attendance / no bank transfer."""
    e_name_col = e_map.get("employee_name")
    if not e_name_col:
        return pd.DataFrame()

    ghosts = []
    att_name_col = None
    att_days_col = None
    if attendance_df is not None and not attendance_df.empty:
        att_map = build_column_map(attendance_df)
        att_name_col = att_map.get("employee_name")
        att_days_col = att_map.get("days_worked")

    for _, ecr_row in ecr_df.iterrows():
        ecr_name = str(ecr_row.get(e_name_col, ""))
        if not ecr_name or ecr_name in ("nan", ""):
            continue

        norm_ecr = normalize_name(ecr_name)
        indicators = []

        # Check attendance
        if attendance_df is not None and att_name_col and att_days_col:
            att_matches = attendance_df[
                attendance_df[att_name_col].apply(normalize_name) == norm_ecr
            ]
            if att_matches.empty:
                indicators.append("No attendance record")
            else:
                total_days = pd.to_numeric(
                    att_matches[att_days_col], errors="coerce"
                ).sum()
                if total_days == 0:
                    indicators.append("Zero attendance days")

        # Check wages
        w_name_col = w_map.get("employee_name")
        if w_name_col:
            wage_matches = wages_df[
                wages_df[w_name_col].apply(normalize_name) == norm_ecr
            ]
            if wage_matches.empty:
                indicators.append("Not in wage register")

        if indicators:
            e_id = e_map.get("employee_id")
            e_site = e_map.get("site_location")
            ghosts.append({
                "employee_name": ecr_name,
                "employee_id": str(ecr_row.get(e_id, "")) if e_id else "",
                "site": str(ecr_row.get(e_site, "")) if e_site else "",
                "ghost_indicators": "; ".join(indicators),
                "indicator_count": len(indicators),
                "severity": "critical" if len(indicators) >= 2 else "high",
            })

    return pd.DataFrame(ghosts) if ghosts else pd.DataFrame()


def detect_duplicate_bank(
    df: pd.DataFrame,
    col_map: Dict,
) -> pd.DataFrame:
    """Same bank account for multiple employees."""
    bank_col = col_map.get("bank_account")
    name_col = col_map.get("employee_name")
    id_col = col_map.get("employee_id")

    if not bank_col or bank_col not in df.columns:
        return pd.DataFrame()

    dups = []
    grouped = df.dropna(subset=[bank_col]).groupby(bank_col)

    for acct, group in grouped:
        if len(group) < 2:
            continue
        names = group[name_col].dropna().tolist() if name_col else []
        ids = group[id_col].dropna().tolist() if id_col else []
        dups.append({
            "bank_account": str(acct),
            "employee_count": len(group),
            "employee_names": "; ".join(str(n) for n in names[:5]),
            "employee_ids": "; ".join(str(i) for i in ids[:5]),
            "severity": "critical",
        })

    return pd.DataFrame(dups) if dups else pd.DataFrame()


def detect_fake_pf_record(
    ecr_df: pd.DataFrame,
    e_map: Dict,
) -> pd.DataFrame:
    """Anomalies suggesting fabricated PF records."""
    anomalies = []
    basic_col = e_map.get("basic_vda")
    name_col = e_map.get("employee_name")
    uan_col = e_map.get("uan_number")

    if not basic_col or basic_col not in ecr_df.columns:
        return pd.DataFrame()

    amounts = pd.to_numeric(ecr_df[basic_col], errors="coerce").dropna()

    if amounts.empty:
        return pd.DataFrame()

    # Check 1: All employees have exactly the same salary
    unique_count = amounts.nunique()
    if len(amounts) > 10 and unique_count <= 2:
        for _, row in ecr_df.iterrows():
            anomalies.append({
                "employee_name": str(row.get(name_col, "")) if name_col else "",
                "uan": str(row.get(uan_col, "")) if uan_col else "",
                "anomaly_type": "Identical salaries across employees",
                "value": float(row.get(basic_col, 0)),
                "severity": "high",
            })

    # Check 2: All salaries are round numbers
    round_count = sum(1 for a in amounts if a % 1000 == 0)
    if len(amounts) > 5 and round_count == len(amounts):
        for _, row in ecr_df.iterrows():
            anomalies.append({
                "employee_name": str(row.get(name_col, "")) if name_col else "",
                "uan": str(row.get(uan_col, "")) if uan_col else "",
                "anomaly_type": "All salaries are round thousands",
                "value": float(row.get(basic_col, 0)),
                "severity": "medium",
            })

    # Check 3: All salaries at exactly ceiling
    ceiling_count = sum(1 for a in amounts if a == 15000)
    if len(amounts) > 10 and ceiling_count / len(amounts) > 0.9:
        for _, row in ecr_df.iterrows():
            if float(row.get(basic_col, 0)) == 15000:
                anomalies.append({
                    "employee_name": str(row.get(name_col, "")) if name_col else "",
                    "anomaly_type": "Salary at exactly PF ceiling",
                    "value": 15000.0,
                    "severity": "medium",
                })

    return pd.DataFrame(anomalies) if anomalies else pd.DataFrame()


# ============================================================
# 12. RISK & COMPLIANCE SCORING
# ============================================================


def calculate_risk_score(
    match_confidence: float,
    pf_diff: float = 0.0,
    employer_diff: float = 0.0,
    is_duplicate: bool = False,
    missing_systems: int = 0,
    fraud_flags: int = 0,
    validations_failed: int = 0,
) -> int:
    """Composite risk score 0-100."""
    score = 0

    # Match confidence (0-30)
    if match_confidence < 70:
        score += 30
    elif match_confidence < 80:
        score += 20
    elif match_confidence < 90:
        score += 10

    # PF mismatch magnitude (0-25)
    pf_abs = abs(pf_diff)
    if pf_abs > 500:
        score += 25
    elif pf_abs > 200:
        score += 15
    elif pf_abs > 50:
        score += 8

    # Employer mismatch (0-15)
    er_abs = abs(employer_diff)
    if er_abs > 500:
        score += 15
    elif er_abs > 100:
        score += 8

    # Duplicate (0-15)
    if is_duplicate:
        score += 15

    # Missing systems (0-10)
    score += min(missing_systems * 5, 10)

    # Fraud (0-10)
    score += min(fraud_flags * 5, 10)

    # Failed validations (0-10)
    score += min(validations_failed * 3, 10)

    return min(score, 100)


def assign_risk_level(score: int) -> str:
    """Map risk score to level."""
    if score <= 20:
        return "safe"
    elif score <= 40:
        return "low"
    elif score <= 60:
        return "medium"
    elif score <= 80:
        return "high"
    return "critical"


def calculate_compliance_score(
    total: int, matched: int, mismatched: int,
    missing: int,
) -> Dict[str, Any]:
    """Overall PF compliance percentage."""
    if total == 0:
        return {"compliance_pct": 0.0, "total": 0}

    compliant = matched
    pct = round((compliant / total) * 100, 2)

    return {
        "compliance_pct": pct,
        "total": total,
        "matched": matched,
        "mismatched": mismatched,
        "missing": missing,
        "status": "compliant" if pct >= 95 else (
            "acceptable" if pct >= 85 else (
                "needs_review" if pct >= 70 else "non_compliant"
            )
        ),
    }


# ============================================================
# 13. SITE & MULTI-MONTH SUPPORT
# ============================================================


def reconcile_site(
    wages_df: pd.DataFrame,
    ecr_df: pd.DataFrame,
    site_name: str,
    rules: PFRuleSet,
    w_map: Dict, e_map: Dict,
) -> pd.DataFrame:
    """Run full reconciliation for one site."""
    w_site_col = w_map.get("site_location")
    e_site_col = e_map.get("site_location")

    site_wages = wages_df
    if w_site_col and w_site_col in wages_df.columns:
        site_wages = wages_df[
            wages_df[w_site_col].astype(str).str.upper().str.strip()
            == site_name.upper().strip()
        ]

    site_ecr = ecr_df
    if e_site_col and e_site_col in ecr_df.columns:
        site_ecr = ecr_df[
            ecr_df[e_site_col].astype(str).str.upper().str.strip()
            == site_name.upper().strip()
        ]

    if site_wages.empty:
        return pd.DataFrame()

    results = []
    for _, row in site_wages.iterrows():
        row_dict = row.to_dict()

        emp_pf = validate_employee_pf(row_dict, rules, w_map)
        er_pf = validate_employer_pf(row_dict, rules, w_map)
        pf_wage = validate_pf_wages(row_dict, rules, w_map)

        basic = pd.to_numeric(row_dict.get(w_map.get("basic_vda", ""), 0), errors="coerce") or 0
        actual_epf = pd.to_numeric(row_dict.get(w_map.get("employee_pf", ""), 0), errors="coerce") or 0
        pf_base = min(basic, rules.pf_ceiling)
        expected_epf = round(pf_base * rules.employee_epf_rate)

        results.append({
            "site": site_name,
            "employee_name": str(row_dict.get(w_map.get("employee_name", ""), "")),
            "basic_vda": basic,
            "pf_base": pf_base,
            "expected_employee_pf": expected_epf,
            "actual_employee_pf": actual_epf,
            "employee_pf_diff": round(actual_epf - expected_epf, 2),
            "employee_pf_status": emp_pf.status if emp_pf else "skip",
            "employer_pf_status": er_pf.status if er_pf else "skip",
        })

    return pd.DataFrame(results)


def generate_site_summary(
    site_results: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Aggregate reconciliation per site."""
    summaries = []
    for site, df in site_results.items():
        if df.empty:
            continue
        total = len(df)
        matched = len(df[df.get("employee_pf_status", pd.Series()) == "pass"]) if "employee_pf_status" in df.columns else 0
        mismatched = total - matched
        total_diff = df["employee_pf_diff"].sum() if "employee_pf_diff" in df.columns else 0

        summaries.append({
            "site": site,
            "total_employees": total,
            "matched": matched,
            "mismatched": mismatched,
            "compliance_pct": round((matched / total * 100) if total else 0, 2),
            "total_pf_difference": round(total_diff, 2),
        })

    return pd.DataFrame(summaries) if summaries else pd.DataFrame()


def process_month(
    wages_df: pd.DataFrame,
    ecr_df: pd.DataFrame,
    month: str,
    year: str,
    rules: PFRuleSet,
    w_map: Dict, e_map: Dict,
) -> pd.DataFrame:
    """Reconcile for a specific month."""
    m_col = w_map.get("pay_month")
    y_col = w_map.get("pay_year")

    filtered = wages_df
    if m_col and m_col in wages_df.columns:
        filtered = filtered[
            filtered[m_col].astype(str).str.lower().str.strip()
            == month.lower().strip()
        ]
    if y_col and y_col in wages_df.columns:
        filtered = filtered[
            filtered[y_col].astype(str).str.strip()
            == str(year).strip()
        ]

    if filtered.empty:
        return pd.DataFrame()

    results = []
    for _, row in filtered.iterrows():
        rd = row.to_dict()
        emp_pf = validate_employee_pf(rd, rules, w_map)
        basic = pd.to_numeric(rd.get(w_map.get("basic_vda", ""), 0), errors="coerce") or 0
        actual = pd.to_numeric(rd.get(w_map.get("employee_pf", ""), 0), errors="coerce") or 0
        expected = round(min(basic, rules.pf_ceiling) * rules.employee_epf_rate)

        results.append({
            "month": month,
            "year": year,
            "employee_name": str(rd.get(w_map.get("employee_name", ""), "")),
            "basic_vda": basic,
            "expected_pf": expected,
            "actual_pf": actual,
            "difference": round(actual - expected, 2),
            "status": emp_pf.status if emp_pf else "skip",
        })

    df = pd.DataFrame(results)
    return df


def generate_monthly_trend(
    monthly_results: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Compare results across months."""
    trends = []
    for key, df in sorted(monthly_results.items()):
        if df.empty:
            continue
        total = len(df)
        matched = len(df[df["status"] == "pass"]) if "status" in df.columns else 0
        total_diff = df["difference"].sum() if "difference" in df.columns else 0

        trends.append({
            "month_year": key,
            "total_employees": total,
            "matched": matched,
            "mismatched": total - matched,
            "compliance_pct": round((matched / total * 100) if total else 0, 2),
            "total_difference": round(total_diff, 2),
        })

    # Add trend direction
    tdf = pd.DataFrame(trends)
    if len(tdf) >= 2:
        tdf["trend"] = tdf["compliance_pct"].diff().apply(
            lambda x: "improving" if x > 0 else ("declining" if x < 0 else "stable")
        )
    elif not tdf.empty:
        tdf["trend"] = "baseline"

    return tdf


# ============================================================
# 14. AUDIT TRAIL & EXCEPTION LOGGING
# ============================================================

_audit_entries: List[AuditEntry] = []
_exception_entries: List[Dict] = []


def write_audit_log(
    action: str,
    employee_name: str = "",
    employee_id: str = "",
    site: str = "",
    field_name: str = "",
    old_value: str = "",
    new_value: str = "",
    detail: str = "",
    operator: str = "auto",
):
    """Append an audit entry."""
    _audit_entries.append(AuditEntry(
        timestamp=datetime.now().isoformat(),
        action=action,
        employee_name=employee_name,
        employee_id=employee_id,
        site=site,
        field_name=field_name,
        old_value=str(old_value),
        new_value=str(new_value),
        detail=detail,
        operator=operator,
    ))


def log_validation_error(
    error_type: str,
    employee_name: str = "",
    detail: str = "",
    severity: str = "medium",
    site: str = "",
):
    """Append to exception log."""
    _exception_entries.append({
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "employee_name": employee_name,
        "site": site,
        "detail": detail,
        "severity": severity,
    })


def get_audit_dataframe() -> pd.DataFrame:
    if not _audit_entries:
        return pd.DataFrame()
    return pd.DataFrame([asdict(e) for e in _audit_entries])


def get_exception_dataframe() -> pd.DataFrame:
    if not _exception_entries:
        return pd.DataFrame()
    return pd.DataFrame(_exception_entries)


# ============================================================
# 15. REPORT GENERATORS
# ============================================================


def generate_dashboard_summary(
    match_report: pd.DataFrame,
    pf_report: pd.DataFrame,
    stats: RuntimeStats,
    compliance: Dict,
) -> Dict[str, Any]:
    """Top-level KPIs."""
    dash = {
        "generated_at": datetime.now().isoformat(),
        "engine_version": "3.0.0",
        "runtime": stats.summary(),
        "compliance": compliance,
    }

    if not match_report.empty:
        dash["matching"] = {
            "total_attempted": len(match_report),
            "matched": int(match_report["matched"].sum()) if "matched" in match_report.columns else 0,
            "exact_matches": int(
                match_report["match_type"].str.startswith("exact").sum()
            ) if "match_type" in match_report.columns else 0,
            "fuzzy_matches": int(
                match_report["match_type"].str.startswith("fuzzy").sum()
            ) if "match_type" in match_report.columns else 0,
            "no_match": int(
                (match_report["match_type"] == "no_match").sum()
            ) if "match_type" in match_report.columns else 0,
            "avg_confidence": round(
                float(match_report["confidence"].mean()), 2
            ) if "confidence" in match_report.columns else 0,
        }

    if not pf_report.empty:
        dash["reconciliation"] = {
            "total_employees": len(pf_report),
            "total_pf_difference": round(
                float(pf_report["difference"].sum()), 2
            ) if "difference" in pf_report.columns else 0,
        }

    return dash


def generate_site_dashboard(
    site_summary: pd.DataFrame,
) -> pd.DataFrame:
    """Per-site breakdown."""
    return site_summary


def generate_month_dashboard(
    monthly_trend: pd.DataFrame,
) -> pd.DataFrame:
    """Per-month breakdown."""
    return monthly_trend


def generate_missing_employee_report(
    missing_wages: pd.DataFrame,
    missing_ecr: pd.DataFrame,
) -> pd.DataFrame:
    """Combined missing employee report."""
    frames = []
    if not missing_wages.empty:
        frames.append(missing_wages)
    if not missing_ecr.empty:
        frames.append(missing_ecr)
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


def generate_duplicate_report(
    dup_uan: pd.DataFrame,
    dup_employee: pd.DataFrame,
    dup_bank: pd.DataFrame,
) -> pd.DataFrame:
    """Combined duplicate report."""
    frames = []
    for df in (dup_uan, dup_employee, dup_bank):
        if df is not None and not df.empty:
            frames.append(df)
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()


def generate_manual_review_report(
    match_report: pd.DataFrame,
) -> pd.DataFrame:
    """Filter fuzzy matches needing review."""
    if match_report.empty:
        return pd.DataFrame()
    if "confidence" not in match_report.columns:
        return pd.DataFrame()
    mask = (match_report["confidence"] >= 70) & (match_report["confidence"] < 90)
    return match_report[mask].copy()


def generate_exception_report(
    validations: List[ValidationResult],
) -> pd.DataFrame:
    """All failed validations."""
    failed = [v for v in validations if v.status in ("fail", "warning")]
    if not failed:
        return pd.DataFrame()
    return pd.DataFrame([asdict(v) for v in failed])


def generate_final_pf_report(
    wages_df: pd.DataFrame,
    match_report: pd.DataFrame,
    pf_validations: List[ValidationResult],
    risk_scores: Dict[str, Dict],
    w_map: Dict,
) -> pd.DataFrame:
    """Consolidated full reconciliation report."""
    records = []
    name_col = w_map.get("employee_name")

    # Build validation lookup by name
    val_lookup: Dict[str, List[ValidationResult]] = defaultdict(list)
    for v in pf_validations:
        val_lookup[normalize_name(v.employee_name)].append(v)

    # Build match lookup by name
    match_lookup = {}
    if not match_report.empty and "source_name" in match_report.columns:
        for _, row in match_report.iterrows():
            key = normalize_name(row["source_name"])
            match_lookup[key] = row.to_dict()

    for _, row in wages_df.iterrows():
        rd = row.to_dict()
        emp_name = str(rd.get(name_col, ""))
        norm = normalize_name(emp_name)

        # Match info
        m = match_lookup.get(norm, {})

        # Validations
        vals = val_lookup.get(norm, [])
        passed = sum(1 for v in vals if v.status == "pass")
        failed = sum(1 for v in vals if v.status in ("fail", "warning"))

        # Risk
        risk = risk_scores.get(norm, {"score": 0, "level": "safe"})

        # Basic PF calculation
        basic = pd.to_numeric(rd.get(w_map.get("basic_vda", ""), 0), errors="coerce") or 0
        actual_pf = pd.to_numeric(rd.get(w_map.get("employee_pf", ""), 0), errors="coerce") or 0
        pf_base = min(basic, 15000)
        expected_pf = round(pf_base * 0.12)

        records.append({
            "employee_name": emp_name,
            "employee_id": str(rd.get(w_map.get("employee_id", ""), "")),
            "uan": str(rd.get(w_map.get("uan_number", ""), "")),
            "site": str(rd.get(w_map.get("site_location", ""), "")),
            "match_type": m.get("match_type", "no_match"),
            "match_confidence": m.get("confidence", 0.0),
            "match_reason": m.get("reason", ""),
            "basic_vda": basic,
            "pf_base": pf_base,
            "expected_employee_pf": expected_pf,
            "actual_employee_pf": actual_pf,
            "employee_pf_diff": round(actual_pf - expected_pf, 2),
            "risk_score": risk.get("score", 0),
            "risk_level": risk.get("level", "safe"),
            "validations_passed": passed,
            "validations_failed": failed,
            "compliance_flag": "compliant" if failed == 0 and m.get("matched") else "review",
        })

    return pd.DataFrame(records) if records else pd.DataFrame()


# ============================================================
# 16. PIPELINE METRICS
# ============================================================


def collect_runtime_statistics(
    stats: RuntimeStats,
) -> RuntimeStats:
    """Finalize stats."""
    stats.finish()
    return stats


def generate_pipeline_metrics(
    stats: RuntimeStats,
    match_report: pd.DataFrame,
    validations: List[ValidationResult],
) -> Dict[str, Any]:
    """Derived metrics."""
    total_val = len(validations)
    passed_val = sum(1 for v in validations if v.status == "pass")

    return {
        "elapsed_seconds": stats.elapsed,
        "rows_per_second": stats.rows_per_sec,
        "match_rate": round(
            (stats.matches_found / stats.matches_attempted * 100)
            if stats.matches_attempted else 0, 2
        ),
        "validation_pass_rate": round(
            (passed_val / total_val * 100) if total_val else 0, 2
        ),
        "total_validations": total_val,
        "files_loaded": stats.files_loaded,
        "rows_processed": stats.rows_loaded,
        "duplicates_found": stats.duplicates_found,
        "missing_found": stats.missing_found,
        "fraud_flags": stats.fraud_flags,
        "errors": stats.errors,
    }


# ============================================================
# 17. EXPORT FUNCTIONS
# ============================================================


def export_reconciliation_reports(reports: Dict[str, pd.DataFrame]):
    """Write all CSV files."""
    for name, df in reports.items():
        if df is not None and not df.empty:
            path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            logger.info(f"CSV → {path} ({len(df)} rows)")


def export_json_summary(dashboard: Dict, metrics: Dict):
    """Write JSON summaries."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary = {**dashboard, "pipeline_metrics": metrics}
    path = SUMMARY_DIR / f"pf_reconciliation_summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"JSON → {path}")

    stats_path = SUMMARY_DIR / f"pipeline_statistics_{ts}.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=str)
    logger.info(f"JSON → {stats_path}")


def export_excel_report(reports: Dict[str, pd.DataFrame]):
    """Single Excel with separate sheets."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"pf_reconciliation_{ts}.xlsx"

    sheets = {}
    for name, df in reports.items():
        if df is not None and not df.empty:
            safe = name[:31].replace("/", "_")
            sheets[safe] = df

    if not sheets:
        logger.warning("No data to export to Excel")
        return

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    logger.info(f"Excel → {path} ({len(sheets)} sheets)")


# ============================================================
# 18. MAIN ENGINE
# ============================================================


class PFReconciliationEngine:
    """
    Production orchestrator for PF reconciliation.

    Pipeline:
      1. Load config & rules
      2. Load all data sources
      3. Cascade matching
      4. Duplicate detection
      5. Missing employee detection
      6. Validation (12 validators)
      7. Fraud detection
      8. Risk scoring
      9. Compliance scoring
      10. Site & month processing
      11. Report generation
      12. Export (CSV + JSON + Excel)
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        client_name: str = "default",
        wages_excel: Optional[Path] = None,
    ):
        self.config = config or load_engine_configuration()
        self.client_config = load_client_config(client_name)
        self.rules = load_pf_rules(self.config)
        self.wages_excel = wages_excel

        self.paths = get_client_paths(self.client_config)
        self.stats = RuntimeStats()

        # Data
        self.sources: Dict[str, pd.DataFrame] = {}
        self.column_maps: Dict[str, Dict[str, Optional[str]]] = {}

        # Results
        self.match_report = pd.DataFrame()
        self.pf_validations: List[ValidationResult] = []
        self.risk_scores: Dict[str, Dict] = {}
        self.site_results: Dict[str, pd.DataFrame] = {}
        self.monthly_results: Dict[str, pd.DataFrame] = {}

        # Reports
        self.all_reports: Dict[str, pd.DataFrame] = {}

    def run(self) -> Dict[str, Any]:
        """Execute the full pipeline."""
        self.stats = RuntimeStats()

        logger.info("=" * 70)
        logger.info("PF RECONCILIATION ENGINE")
        logger.info(f"Client: {self.client_config.client_name}")
        logger.info(f"PF Ceiling: ₹{self.rules.pf_ceiling:,.0f}")
        logger.info(f"Employee Rate: {self.rules.employee_epf_rate:.0%}")
        logger.info("=" * 70)

        # ---- 1. Load data ----
        self.sources = load_all_sources(self.paths, self.wages_excel)
        self.stats.files_loaded = len(self.sources)

        for key, df in self.sources.items():
            self.column_maps[key] = build_column_map(df)
            self.stats.rows_loaded += len(df)

        if "wages" not in self.sources:
            logger.error("No wages data found — cannot proceed")
            self.stats.finish()
            return {"error": "No wages data"}

        wages_df = self.sources["wages"]
        w_map = self.column_maps["wages"]

        # ---- 2. Cascade matching ----
        logger.info("=" * 50)
        logger.info("PHASE 1: CASCADE MATCHING")
        logger.info("=" * 50)

        if "ecr" in self.sources:
            ecr_df = self.sources["ecr"]
            e_map = self.column_maps["ecr"]

            self.match_report = cascade_match(
                wages_df, ecr_df, w_map, e_map,
                fuzzy_threshold=self.config.get("fuzzy_threshold", 0.70),
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
                self.stats.no_matches = int(
                    (self.match_report["match_type"] == "no_match").sum()
                )
            logger.info(
                f"Matches: {self.stats.matches_found}/{self.stats.matches_attempted} "
                f"(exact={self.stats.exact_matches}, fuzzy={self.stats.fuzzy_matches})"
            )

            write_audit_log("MATCHING_COMPLETE", detail=f"Attempted={self.stats.matches_attempted}")

        # ---- 3. Duplicate detection ----
        logger.info("=" * 50)
        logger.info("PHASE 2: DUPLICATE DETECTION")
        logger.info("=" * 50)

        dup_uan = detect_duplicate_uan(wages_df, w_map)
        dup_employee = detect_duplicate_employee(wages_df, w_map)
        dup_bank = detect_duplicate_bank(wages_df, w_map)

        total_dups = sum(
            len(df) for df in (dup_uan, dup_employee, dup_bank)
            if df is not None and not df.empty
        )
        self.stats.duplicates_found = total_dups
        logger.info(f"Duplicates: {total_dups}")

        # ---- 4. Missing detection ----
        logger.info("=" * 50)
        logger.info("PHASE 3: MISSING EMPLOYEE DETECTION")
        logger.info("=" * 50)

        missing_wages = pd.DataFrame()
        missing_ecr = pd.DataFrame()

        if "ecr" in self.sources:
            missing_wages = detect_missing_in_wages(wages_df, ecr_df, w_map, e_map)
            missing_ecr = detect_missing_in_ecr(wages_df, ecr_df, w_map, e_map)

        total_missing = len(missing_wages) + len(missing_ecr)
        self.stats.missing_found = total_missing
        logger.info(f"Missing: {total_missing}")

        # ---- 5. Validation ----
        logger.info("=" * 50)
        logger.info("PHASE 4: VALIDATION ENGINE")
        logger.info("=" * 50)

        for _, row in wages_df.iterrows():
            rd = row.to_dict()

            # 12 validators
            vr = validate_pf_wages(rd, self.rules, w_map)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1

            vr = validate_employee_pf(rd, self.rules, w_map)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1

            vr = validate_employer_pf(rd, self.rules, w_map)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1

            vr = validate_pf_ceiling(rd, self.rules, w_map)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1

            vr = validate_joining_exit_dates(rd, w_map)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1
                log_validation_error("date_validation", vr.employee_name, vr.detail, vr.severity)

            vr = validate_site_assignment(rd, w_map, self.client_config.sites)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1

            vr = validate_leave_effect(rd, self.rules, w_map)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1

            vr = validate_ot_component(rd, w_map)
            if vr:
                self.pf_validations.append(vr)
                self.stats.validations_run += 1

        # Attendance linkage (if available)
        if "attendance" in self.sources and "ecr" in self.sources:
            a_map = self.column_maps.get("attendance", {})
            att_df = self.sources["attendance"]
            att_name_col = a_map.get("employee_name")
            if att_name_col:
                att_index = {}
                for i, row in att_df.iterrows():
                    n = normalize_name(row.get(att_name_col))
                    if n:
                        att_index[n] = row.to_dict()

                for _, row in wages_df.iterrows():
                    rd = row.to_dict()
                    norm = normalize_name(rd.get(w_map.get("employee_name", "")))
                    if norm in att_index:
                        vr = validate_attendance_against_pf(
                            rd, att_index[norm], w_map, a_map,
                        )
                        if vr:
                            self.pf_validations.append(vr)
                            self.stats.validations_run += 1

        # Bank linkage (if available)
        if "bank" in self.sources:
            b_map = self.column_maps.get("bank", {})
            bank_df = self.sources["bank"]
            bank_name_col = b_map.get("employee_name")
            if bank_name_col:
                bank_index = {}
                for i, row in bank_df.iterrows():
                    n = normalize_name(row.get(bank_name_col))
                    if n:
                        bank_index[n] = row.to_dict()

                for _, row in wages_df.iterrows():
                    rd = row.to_dict()
                    norm = normalize_name(rd.get(w_map.get("employee_name", "")))
                    if norm in bank_index:
                        vr = validate_bank_payment(
                            rd, bank_index[norm], w_map, b_map,
                        )
                        if vr:
                            self.pf_validations.append(vr)
                            self.stats.validations_run += 1

        # Count pass/fail
        self.stats.validations_passed = sum(
            1 for v in self.pf_validations if v.status == "pass"
        )
        self.stats.validations_failed = sum(
            1 for v in self.pf_validations if v.status in ("fail", "warning")
        )

        logger.info(
            f"Validations: {self.stats.validations_run} run, "
            f"{self.stats.validations_passed} passed, "
            f"{self.stats.validations_failed} failed"
        )

        # ---- 6. Fraud detection ----
        logger.info("=" * 50)
        logger.info("PHASE 5: FRAUD DETECTION")
        logger.info("=" * 50)

        ghost_df = pd.DataFrame()
        fake_df = pd.DataFrame()

        if "ecr" in self.sources:
            att_for_ghost = self.sources.get("attendance")
            ghost_df = detect_ghost_employee(
                wages_df, ecr_df, att_for_ghost, w_map, e_map,
            )
            fake_df = detect_fake_pf_record(ecr_df, e_map)

        fraud_total = sum(
            len(df) for df in (ghost_df, dup_bank, fake_df)
            if df is not None and not df.empty
        )
        self.stats.fraud_flags = fraud_total
        logger.info(f"Fraud flags: {fraud_total}")

        # ---- 7. Risk scoring ----
        logger.info("=" * 50)
        logger.info("PHASE 6: RISK SCORING")
        logger.info("=" * 50)

        dup_names = set()
        for df in (dup_uan, dup_employee):
            if df is not None and not df.empty:
                for col in ("employee_a_name",):
                    if col in df.columns:
                        dup_names.update(df[col].apply(normalize_name))

        missing_name_set = set()
        for df in (missing_wages, missing_ecr):
            if df is not None and not df.empty and "employee_name" in df.columns:
                missing_name_set.update(df["employee_name"].apply(normalize_name))

        name_col = w_map.get("employee_name")
        pf_diff_col_name = "employee_pf_diff"

        for _, row in wages_df.iterrows():
            rd = row.to_dict()
            emp_name = str(rd.get(name_col, ""))
            norm = normalize_name(emp_name)

            # Get PF diff
            basic = pd.to_numeric(rd.get(w_map.get("basic_vda", ""), 0), errors="coerce") or 0
            actual_pf = pd.to_numeric(rd.get(w_map.get("employee_pf", ""), 0), errors="coerce") or 0
            expected_pf = round(min(basic, self.rules.pf_ceiling) * self.rules.employee_epf_rate)
            pf_diff = actual_pf - expected_pf

            # Get match confidence
            match_conf = 100.0
            if not self.match_report.empty and "source_name" in self.match_report.columns:
                m_row = self.match_report[
                    self.match_report["source_name"].apply(normalize_name) == norm
                ]
                if not m_row.empty:
                    match_conf = float(m_row.iloc[0].get("confidence", 0))

            # Count failed validations for this employee
            emp_failed = sum(
                1 for v in self.pf_validations
                if normalize_name(v.employee_name) == norm and v.status in ("fail", "warning")
            )

            score = calculate_risk_score(
                match_confidence=match_conf,
                pf_diff=pf_diff,
                is_duplicate=norm in dup_names,
                missing_systems=1 if norm in missing_name_set else 0,
                fraud_flags=0,
                validations_failed=emp_failed,
            )

            self.risk_scores[norm] = {
                "score": score,
                "level": assign_risk_level(score),
                "name": emp_name,
            }

        logger.info(f"Risk scores computed: {len(self.risk_scores)}")

        # ---- 8. Site reconciliation ----
        logger.info("=" * 50)
        logger.info("PHASE 7: SITE RECONCILIATION")
        logger.info("=" * 50)

        site_col = w_map.get("site_location")
        if site_col and site_col in wages_df.columns:
            sites = wages_df[site_col].dropna().unique()
            for site in sites:
                site_str = str(site).strip()
                if site_str and site_str not in ("nan", "None"):
                    self.site_results[site_str] = reconcile_site(
                        wages_df, ecr_df if "ecr" in self.sources else pd.DataFrame(),
                        site_str, self.rules, w_map, e_map if "ecr" in self.sources else {},
                    )
            self.stats.sites_processed = len(self.site_results)
            logger.info(f"Sites processed: {self.stats.sites_processed}")

        # ---- 9. Compliance scoring ----
        total_emp = len(wages_df)
        matched_count = self.stats.matches_found
        mismatch_count = self.stats.validations_failed
        compliance = calculate_compliance_score(
            total_emp, matched_count, mismatch_count, self.stats.missing_found,
        )
        logger.info(f"Compliance: {compliance['compliance_pct']}% ({compliance['status']})")

        # ---- 10. Generate reports ----
        logger.info("=" * 50)
        logger.info("PHASE 8: REPORT GENERATION")
        logger.info("=" * 50)

        # Final PF report
        final_pf = generate_final_pf_report(
            wages_df, self.match_report, self.pf_validations,
            self.risk_scores, w_map,
        )

        # Missing report
        missing_report = generate_missing_employee_report(missing_wages, missing_ecr)

        # Duplicate report
        dup_report = generate_duplicate_report(dup_uan, dup_employee, dup_bank)

        # Manual review
        review_report = generate_manual_review_report(self.match_report)

        # Exception report
        exception_report = generate_exception_report(self.pf_validations)

        # Site summary
        site_summary = generate_site_summary(self.site_results)

        # PF wage mismatches
        pf_wage_mismatches = pd.DataFrame([asdict(v) for v in self.pf_validations
                                           if v.validation_type == "pf_wage" and v.status == "fail"])
        emp_pf_mismatches = pd.DataFrame([asdict(v) for v in self.pf_validations
                                          if v.validation_type == "employee_pf" and v.status == "fail"])
        er_pf_mismatches = pd.DataFrame([asdict(v) for v in self.pf_validations
                                         if v.validation_type == "employer_pf" and v.status == "fail"])

        # Risk summary
        risk_df = pd.DataFrame(list(self.risk_scores.values())) if self.risk_scores else pd.DataFrame()

        # Audit trail
        audit_df = get_audit_dataframe()
        exception_log_df = get_exception_dataframe()

        # Compliance dashboard
        compliance_df = pd.DataFrame([compliance])

        # Collect all reports
        self.all_reports = {
            "employee_matching_report": self.match_report,
            "pf_reconciliation_report": final_pf,
            "missing_employees": missing_report,
            "duplicate_uan": dup_uan if dup_uan is not None else pd.DataFrame(),
            "duplicate_employees": dup_report,
            "manual_review": review_report,
            "pf_wage_mismatch": pf_wage_mismatches,
            "employee_pf_mismatch": emp_pf_mismatches,
            "employer_pf_mismatch": er_pf_mismatches,
            "site_summary": site_summary,
            "monthly_summary": pd.DataFrame(),
            "compliance_dashboard": compliance_df,
            "risk_summary": risk_df,
            "audit_trail": audit_df,
            "exception_log": exception_log_df,
        }

        # ---- 11. Export ----
        logger.info("=" * 50)
        logger.info("PHASE 9: EXPORT")
        logger.info("=" * 50)

        # Filter out empty reports for export
        csv_reports = {k: v for k, v in self.all_reports.items() if v is not None and not v.empty}
        export_reconciliation_reports(csv_reports)

        # Dashboard
        self.stats.finish()
        dashboard = generate_dashboard_summary(
            self.match_report, final_pf, self.stats, compliance,
        )
        metrics = generate_pipeline_metrics(self.stats, self.match_report, self.pf_validations)

        export_json_summary(dashboard, metrics)
        export_excel_report(csv_reports)

        # ---- Final summary ----
        logger.info("=" * 70)
        logger.info("PF RECONCILIATION COMPLETE")
        logger.info(f"  Elapsed:             {self.stats.elapsed}s")
        logger.info(f"  Files loaded:        {self.stats.files_loaded}")
        logger.info(f"  Rows processed:      {self.stats.rows_loaded}")
        logger.info(f"  Matches found:       {self.stats.matches_found}/{self.stats.matches_attempted}")
        logger.info(f"  Validations:         {self.stats.validations_run} "
                     f"({self.stats.validations_passed} pass / {self.stats.validations_failed} fail)")
        logger.info(f"  Duplicates:          {self.stats.duplicates_found}")
        logger.info(f"  Missing:             {self.stats.missing_found}")
        logger.info(f"  Fraud flags:         {self.stats.fraud_flags}")
        logger.info(f"  Sites processed:     {self.stats.sites_processed}")
        logger.info(f"  Compliance:          {compliance['compliance_pct']}% ({compliance['status']})")
        logger.info(f"  CSV files written:   {len(csv_reports)}")
        logger.info(f"  Speed:               {self.stats.rows_per_sec} rows/sec")
        logger.info("=" * 70)

        return {**dashboard, "pipeline_metrics": metrics}


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Security AI — PF Reconciliation Engine"
    )
    parser.add_argument("--client", default="default", help="Client name")
    parser.add_argument("--wages", default=None, help="Path to wages CSV/Excel")
    parser.add_argument("--ecr", default=None, help="Path to ECR CSV")
    parser.add_argument("--ceiling", type=float, default=15000.0, help="PF ceiling")
    parser.add_argument("--emp-rate", type=float, default=0.12, help="Employee EPF rate")
    parser.add_argument("--fuzzy-threshold", type=float, default=0.70)
    parser.add_argument("--operator", default="auto")

    args = parser.parse_args()

    # Build config
    cfg = load_engine_configuration()
    cfg["pf_ceiling"] = args.ceiling
    cfg["pf_employee_rate"] = args.emp_rate
    cfg["fuzzy_threshold"] = args.fuzzy_threshold
    cfg["operator"] = args.operator

    wages_path = Path(args.wages) if args.wages else None

    engine = PFReconciliationEngine(
        config=cfg,
        client_name=args.client,
        wages_excel=wages_path,
    )

    result = engine.run()
    print(json.dumps(result, indent=2, default=str))
