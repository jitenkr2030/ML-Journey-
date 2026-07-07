# security-ai/scripts/site_performance_scoring_engine.py
"""
Production-Grade Site Performance Scoring Engine
Security AI — Multi-Dimensional Site Intelligence System

═══════════════════════════════════════════════════════════════════
 21 MODULES | 90+ FUNCTIONS | MULTI-CLIENT | MULTI-MONTH | AI
═══════════════════════════════════════════════════════════════════

 MODULES:
  1.  Multi-Client Support
  2.  Multi-Month Trend Analysis
  3.  Site Risk Scoring
  4.  KPI Dashboard
  5.  SLA Monitoring
  6.  Shift Coverage Analysis
  7.  Guard Utilization
  8.  Incident Analytics
  9.  Complaint Analytics
  10. Compliance Analytics
  11. AI Site Ranking
  12. Root Cause Analysis
  13. Recommendation Engine
  14. Geographic Analytics
  15. Supervisor Performance
  16. AI Prediction
  17. Site Benchmarking
  18. Audit Trail
  19. Dashboard JSON Export
  20. Executive Summary
  21. ML Readiness & Feature Engineering
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

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "datasets"
CLIENTS_DIR = BASE_DIR / "clients"
RECON_DIR = BASE_DIR / "reconciliation"
OUTPUT_DIR = BASE_DIR / "site_reports"
EXPORT_DIR = BASE_DIR / "exports"
SUMMARY_DIR = BASE_DIR / "summaries"
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

for _d in (DATASET_DIR, CLIENTS_DIR, RECON_DIR, OUTPUT_DIR, EXPORT_DIR, SUMMARY_DIR, LOG_DIR, CONFIG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ============================================================
# PRODUCTION LOGGING
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(funcName)s:%(lineno)d | %(message)s"
)
LOG_DATE = "%Y-%m-%d %H:%M:%S"


def setup_rotating_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("SitePerformance")
    root.setLevel(logging.DEBUG)
    if root.handlers:
        return root
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(ch)
    fh = RotatingFileHandler(
        log_dir / "site_performance.log",
        maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(fh)
    eh = RotatingFileHandler(
        log_dir / "site_performance_errors.log",
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


class Grade(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    AVERAGE = "Average"
    POOR = "Poor"
    CRITICAL = "Critical"


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Trend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


# ============================================================
# MODULE 1 — CONFIGURATION
# ============================================================


@dataclass
class SiteConfig:
    """All scoring weights and thresholds."""
    # KPI weights (must sum to 1.0)
    weight_attendance: float = 0.30
    weight_incident: float = 0.20
    weight_complaint: float = 0.15
    weight_compliance: float = 0.15
    weight_shift_coverage: float = 0.10
    weight_guard_utilization: float = 0.10

    # Grade thresholds
    grade_excellent: float = 90.0
    grade_good: float = 75.0
    grade_average: float = 60.0
    grade_poor: float = 40.0

    # Risk thresholds
    risk_safe: float = 20.0
    risk_low: float = 35.0
    risk_medium: float = 55.0
    risk_high: float = 75.0

    # Incident penalties
    severity_weights: Dict[str, int] = field(default_factory=lambda: {
        "low": 3, "medium": 10, "high": 25, "critical": 50,
    })

    # Complaint penalty per complaint
    complaint_penalty: int = 5

    # SLA thresholds (hours)
    sla_incident_resolution: int = 24
    sla_complaint_closure: int = 48
    sla_guard_replacement: int = 4
    sla_attendance_submission: int = 2

    # Shift requirements
    min_guards_per_shift: int = 2
    shifts_per_day: int = 3

    # Engine
    engine_version: str = "8.0.0"
    operator: str = "auto"


@dataclass
class ClientConfig:
    client_name: str = "default"
    client_id: str = "001"
    sites: List[str] = field(default_factory=list)


@dataclass
class SitePerformance:
    """Complete performance record for one site."""
    site_id: str = ""
    site_name: str = ""
    client: str = ""
    zone: str = ""
    district: str = ""
    city: str = ""
    supervisor: str = ""
    guard_count: int = 0
    month: str = ""
    year: str = ""

    # KPI scores (0-100)
    attendance_score: float = 0.0
    incident_score: float = 0.0
    complaint_score: float = 0.0
    compliance_score: float = 0.0
    shift_coverage_score: float = 0.0
    guard_utilization_score: float = 0.0
    sla_score: float = 0.0

    # Composite
    performance_score: float = 0.0
    risk_score: float = 0.0
    grade: str = Grade.CRITICAL.value
    risk_level: str = RiskLevel.SAFE.value
    trend: str = Trend.STABLE.value

    # Detail counts
    total_attendance: int = 0
    present_count: int = 0
    absent_count: int = 0
    total_incidents: int = 0
    high_incidents: int = 0
    total_complaints: int = 0
    unresolved_complaints: int = 0
    compliance_items: int = 0
    compliant_items: int = 0
    missing_shifts: int = 0
    idle_guards: int = 0
    overloaded_guards: int = 0

    # Root cause & recommendations
    root_causes: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    rank: int = 0


@dataclass
class AuditEntry:
    timestamp: str = ""
    action: str = ""
    module: str = ""
    detail: str = ""
    rows_affected: int = 0
    engine_version: str = "8.0.0"


@dataclass
class RuntimeStats:
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_loaded: int = 0
    rows_loaded: int = 0
    sites_scored: int = 0
    clients_processed: int = 0
    months_processed: int = 0
    modules_run: int = 0
    errors: int = 0

    def finish(self):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        e = self.end_time or time.perf_counter()
        return round(e - self.start_time, 3)

    def summary(self) -> Dict[str, Any]:
        return {"elapsed_seconds": self.elapsed,
                **{k: v for k, v in self.__dict__.items() if k not in ("start_time", "end_time")}}


# Global
_audit_log: List[AuditEntry] = []


def load_config(config_path: Optional[Path] = None) -> SiteConfig:
    cfg = SiteConfig()
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


def audit_log(action: str, module: str = "", detail: str = "", rows: int = 0):
    _audit_log.append(AuditEntry(
        timestamp=datetime.now().isoformat(), action=action,
        module=module, detail=detail, rows_affected=rows,
    ))


def get_audit_dataframe() -> pd.DataFrame:
    return pd.DataFrame([asdict(e) for e in _audit_log]) if _audit_log else pd.DataFrame()


# ============================================================
# FIELD RESOLVER
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "guard_id": ["guard_id", "Guard_ID", "employee_id", "emp_id"],
    "guard_name": ["guard_name", "Guard_Name", "employee_name", "name", "Name"],
    "site_id": ["site_id", "Site_ID", "site", "Site"],
    "site_name": ["site_name", "Site_Name", "location"],
    "client": ["client", "client_name", "Client"],
    "zone": ["zone", "Zone", "region"],
    "district": ["district", "District"],
    "city": ["city", "City"],
    "supervisor": ["supervisor", "Supervisor", "supervisor_name"],
    "status": ["status", "Status", "attendance_status"],
    "date": ["date", "Date", "attendance_date"],
    "shift": ["shift", "Shift", "shift_name"],
    "hours_worked": ["hours_worked", "Hours_Worked", "hours"],
    "severity": ["severity", "Severity", "incident_severity"],
    "incident_type": ["incident_type", "Incident_Type", "type"],
    "complaint_type": ["complaint_type", "Complaint_Type"],
    "resolved": ["resolved", "Resolved", "status"],
    "resolution_date": ["resolution_date", "Resolution_Date", "closed_date"],
    "risk_level": ["risk_level", "Risk_Level"],
    "compliance_type": ["compliance_type", "Compliance_Type", "check_type"],
    "month": ["month", "Month", "pay_month"],
    "year": ["year", "Year", "pay_year"],
    "guard_count_required": ["guard_count_required", "required_guards", "min_guards"],
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


def safe_read_csv(file_path: Path) -> pd.DataFrame:
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
    logger.info(f"Loaded {file_path.name}: {df.shape[0]} × {df.shape[1]}")
    return df


# ============================================================
# MODULE 1 — MULTI-CLIENT SUPPORT
# ============================================================


def list_available_clients() -> List[str]:
    """Discover client directories."""
    clients = []
    if CLIENTS_DIR.exists():
        for d in CLIENTS_DIR.iterdir():
            if d.is_dir():
                clients.append(d.name)
    if not clients:
        clients = ["default"]
    return sorted(clients)


def list_available_months(client: str = "default") -> List[str]:
    """Discover available months for a client."""
    months = []
    client_dir = CLIENTS_DIR / client
    if client_dir.exists():
        for d in sorted(client_dir.iterdir()):
            if d.is_dir():
                months.append(d.name)
    return months


def validate_client_structure(client: str, month: str) -> Dict[str, bool]:
    """Check which data files exist for a client/month."""
    client_dir = CLIENTS_DIR / client / month
    if not client_dir.exists():
        client_dir = DATASET_DIR

    expected = {
        "site_assignments": "site_assignments.csv",
        "attendance": "attendance.csv",
        "incidents": "incidents.csv",
        "complaints": "complaints.csv",
        "compliance": "compliance.csv",
        "payroll": "payroll.csv",
    }
    return {k: (client_dir / v).exists() for k, v in expected.items()}


def load_client_data(
    client: str = "default",
    month: str = "",
) -> Dict[str, pd.DataFrame]:
    """Load data for a specific client/month."""
    client_dir = CLIENTS_DIR / client / month if month else CLIENTS_DIR / client
    if not client_dir.exists():
        client_dir = DATASET_DIR
        logger.info(f"Client dir not found, using dataset dir: {client_dir}")

    sources = {}
    files = {
        "assignments": "site_assignments.csv",
        "attendance": "attendance.csv",
        "incidents": "incidents.csv",
        "complaints": "complaints.csv",
        "compliance": "compliance.csv",
        "payroll": "payroll.csv",
        "bank": "bank.csv",
        "guards": "guards_master.csv",
        "pf": str(RECON_DIR / "pf_reconciliation_report.csv"),
        "esi": str(RECON_DIR / "esi_reconciliation_report.csv"),
    }
    for key, fname in files.items():
        path = Path(fname) if Path(fname).is_absolute() else client_dir / fname
        df = safe_read_csv(path)
        if not df.empty:
            sources[key] = df
    return sources


def load_data() -> Dict[str, pd.DataFrame]:
    """Backward-compatible loader using default dataset dir."""
    return load_client_data("default", "")


# ============================================================
# MODULE 8 — INCIDENT ANALYTICS
# ============================================================


def get_site_guards(assignments: pd.DataFrame, site_id: str) -> List[str]:
    """Get guard IDs assigned to a site."""
    col_map = build_column_map(assignments)
    sid = col_map.get("site_id")
    gid = col_map.get("guard_id")
    if not sid or not gid:
        return []
    guards = assignments[assignments[sid].astype(str).str.strip() == str(site_id).strip()][gid].dropna().tolist()
    return [str(g) for g in guards]


def calculate_attendance_score(
    site_guards: List[str],
    attendance_df: pd.DataFrame,
) -> Tuple[float, int, int, int]:
    """Returns (score, total, present, absent)."""
    if attendance_df.empty or not site_guards:
        return 0.0, 0, 0, 0

    col_map = build_column_map(attendance_df)
    gid = col_map.get("guard_id")
    status = col_map.get("status")
    if not gid or not status:
        return 0.0, 0, 0, 0

    site_att = attendance_df[attendance_df[gid].astype(str).isin(site_guards)]
    if site_att.empty:
        return 0.0, 0, 0, 0

    total = len(site_att)
    present = (site_att[status].astype(str).str.lower() == "present").sum()
    absent = total - present
    score = round((present / total * 100) if total else 0, 2)
    return score, total, int(present), int(absent)


def calculate_incident_score(
    site_guards: List[str],
    incidents_df: pd.DataFrame,
    config: SiteConfig,
) -> Tuple[float, int, int]:
    """Returns (score, total_incidents, high_incidents)."""
    if incidents_df.empty:
        return 100.0, 0, 0

    col_map = build_column_map(incidents_df)
    gid = col_map.get("guard_id")
    sev = col_map.get("severity")
    if not gid:
        return 100.0, 0, 0

    site_inc = incidents_df[incidents_df[gid].astype(str).isin(site_guards)]
    if site_inc.empty:
        return 100.0, 0, 0

    total = len(site_inc)
    penalty = 0
    high_count = 0

    for _, row in site_inc.iterrows():
        severity = str(row.get(sev, "medium")).lower() if sev else "medium"
        weight = config.severity_weights.get(severity, 10)
        penalty += weight
        if severity in ("high", "critical"):
            high_count += 1

    score = max(100 - penalty, 0)
    return round(score, 2), total, high_count


def incident_summary(incidents_df: pd.DataFrame) -> Dict[str, Any]:
    if incidents_df.empty:
        return {}
    col_map = build_column_map(incidents_df)
    sev = col_map.get("severity")
    itype = col_map.get("incident_type")

    summary = {"total": len(incidents_df)}
    if sev:
        summary["by_severity"] = incidents_df[sev].value_counts().to_dict()
    if itype:
        summary["by_type"] = incidents_df[itype].value_counts().to_dict()
    return summary


def repeat_incident_detection(
    incidents_df: pd.DataFrame,
) -> pd.DataFrame:
    """Find guards with repeated incidents."""
    if incidents_df.empty:
        return pd.DataFrame()

    col_map = build_column_map(incidents_df)
    gid = col_map.get("guard_id")
    itype = col_map.get("incident_type")
    if not gid:
        return pd.DataFrame()

    freq = incidents_df.groupby(gid).size()
    repeat = freq[freq >= 3]
    if repeat.empty:
        return pd.DataFrame()

    rows = []
    for guard, count in repeat.items():
        types = []
        if itype:
            types = incidents_df[incidents_df[gid] == guard][itype].dropna().unique().tolist()
        rows.append({
            "guard_id": str(guard),
            "incident_count": int(count),
            "incident_types": "; ".join(str(t) for t in types[:5]),
            "severity": "high" if count >= 5 else "medium",
        })
    return pd.DataFrame(rows)


# ============================================================
# MODULE 9 — COMPLAINT ANALYTICS
# ============================================================


def calculate_complaint_score(
    site_guards: List[str],
    complaints_df: pd.DataFrame,
    config: SiteConfig,
) -> Tuple[float, int, int]:
    """Returns (score, total_complaints, unresolved)."""
    if complaints_df.empty:
        return 100.0, 0, 0

    col_map = build_column_map(complaints_df)
    gid = col_map.get("guard_id")
    resolved = col_map.get("resolved")
    if not gid:
        return 100.0, 0, 0

    site_comp = complaints_df[complaints_df[gid].astype(str).isin(site_guards)]
    if site_comp.empty:
        return 100.0, 0, 0

    total = len(site_comp)
    penalty = total * config.complaint_penalty

    unresolved = 0
    if resolved:
        unresolved = int((~site_comp[resolved].astype(str).str.lower().isin(
            ["yes", "true", "resolved", "closed", "1"]
        )).sum())

    score = max(100 - penalty, 0)
    return round(score, 2), total, unresolved


def complaint_summary(complaints_df: pd.DataFrame) -> Dict[str, Any]:
    if complaints_df.empty:
        return {}
    col_map = build_column_map(complaints_df)
    ctype = col_map.get("complaint_type")
    summary = {"total": len(complaints_df)}
    if ctype:
        summary["by_type"] = complaints_df[ctype].value_counts().to_dict()
    return summary


# ============================================================
# MODULE 10 — COMPLIANCE ANALYTICS
# ============================================================


def calculate_compliance_score(
    site_guards: List[str],
    compliance_df: pd.DataFrame,
) -> Tuple[float, int, int]:
    """Returns (score, total_items, compliant_items)."""
    if compliance_df.empty:
        return 0.0, 0, 0

    col_map = build_column_map(compliance_df)
    gid = col_map.get("guard_id")
    rl = col_map.get("risk_level")
    if not gid:
        return 0.0, 0, 0

    site_comp = compliance_df[compliance_df[gid].astype(str).isin(site_guards)]
    if site_comp.empty:
        return 0.0, 0, 0

    total = len(site_comp)
    if rl:
        compliant = (site_comp[rl].astype(str).str.lower() == "low").sum()
    else:
        compliant = total

    score = round((compliant / total * 100) if total else 0, 2)
    return score, total, int(compliant)


def calculate_pf_compliance(
    site_guards: List[str],
    pf_df: pd.DataFrame,
) -> float:
    if pf_df.empty:
        return 100.0
    col_map = build_column_map(pf_df)
    gid = col_map.get("guard_id") or col_map.get("employee_id")
    status = col_map.get("match_status")
    if not gid or not status:
        return 100.0
    site_pf = pf_df[pf_df[gid].astype(str).isin(site_guards)]
    if site_pf.empty:
        return 100.0
    matched = (site_pf[status].astype(str).str.lower() == "matched").sum()
    return round((matched / len(site_pf) * 100) if len(site_pf) else 100.0, 2)


def calculate_training_compliance(
    site_guards: List[str],
    compliance_df: pd.DataFrame,
) -> float:
    if compliance_df.empty:
        return 100.0
    col_map = build_column_map(compliance_df)
    gid = col_map.get("guard_id")
    ctype = col_map.get("compliance_type")
    status = col_map.get("risk_level") or col_map.get("resolved")
    if not gid:
        return 100.0

    site = compliance_df[compliance_df[gid].astype(str).isin(site_guards)]
    if site.empty:
        return 100.0

    if ctype:
        training = site[site[ctype].astype(str).str.lower().str.contains("train")]
        if training.empty:
            return 100.0
        if status:
            ok = (training[status].astype(str).str.lower().isin(["low", "yes", "complete", "done"])).sum()
            return round((ok / len(training) * 100) if len(training) else 100.0, 2)
    return 100.0


def calculate_psara_compliance(
    site_guards: List[str],
    compliance_df: pd.DataFrame,
) -> float:
    if compliance_df.empty:
        return 100.0
    col_map = build_column_map(compliance_df)
    gid = col_map.get("guard_id")
    ctype = col_map.get("compliance_type")
    if not gid:
        return 100.0

    site = compliance_df[compliance_df[gid].astype(str).isin(site_guards)]
    if site.empty:
        return 100.0

    if ctype:
        psara = site[site[ctype].astype(str).str.lower().str.contains("psara|license")]
        if psara.empty:
            return 100.0
        status = col_map.get("risk_level")
        if status:
            ok = (psara[status].astype(str).str.lower() == "low").sum()
            return round((ok / len(psara) * 100) if len(psara) else 100.0, 2)
    return 100.0


# ============================================================
# MODULE 5 — SLA MONITORING
# ============================================================


def calculate_sla_score(
    site_guards: List[str],
    incidents_df: pd.DataFrame,
    complaints_df: pd.DataFrame,
    config: SiteConfig,
) -> float:
    """Score based on SLA compliance for incidents and complaints."""
    sla_met = 0
    sla_total = 0

    # Incident resolution SLA
    if not incidents_df.empty:
        col_map = build_column_map(incidents_df)
        gid = col_map.get("guard_id")
        date_col = col_map.get("date")
        res_date = col_map.get("resolution_date")

        if gid and date_col:
            site_inc = incidents_df[incidents_df[gid].astype(str).isin(site_guards)]
            for _, row in site_inc.iterrows():
                sla_total += 1
                if res_date and pd.notna(row.get(res_date)):
                    try:
                        created = pd.to_datetime(row.get(date_col))
                        resolved = pd.to_datetime(row.get(res_date))
                        hours = (resolved - created).total_seconds() / 3600
                        if hours <= config.sla_incident_resolution:
                            sla_met += 1
                    except Exception:
                        pass
                else:
                    sla_met += 0  # unresolved = SLA miss

    # Complaint closure SLA
    if not complaints_df.empty:
        col_map = build_column_map(complaints_df)
        gid = col_map.get("guard_id")
        date_col = col_map.get("date")
        res_date = col_map.get("resolution_date")

        if gid and date_col:
            site_comp = complaints_df[complaints_df[gid].astype(str).isin(site_guards)]
            for _, row in site_comp.iterrows():
                sla_total += 1
                if res_date and pd.notna(row.get(res_date)):
                    try:
                        created = pd.to_datetime(row.get(date_col))
                        resolved = pd.to_datetime(row.get(res_date))
                        hours = (resolved - created).total_seconds() / 3600
                        if hours <= config.sla_complaint_closure:
                            sla_met += 1
                    except Exception:
                        pass

    if sla_total == 0:
        return 100.0
    return round((sla_met / sla_total * 100), 2)


# ============================================================
# MODULE 6 — SHIFT COVERAGE ANALYSIS
# ============================================================


def calculate_shift_coverage(
    site_guards: List[str],
    attendance_df: pd.DataFrame,
    config: SiteConfig,
) -> Tuple[float, int]:
    """Returns (coverage_score, missing_shifts)."""
    if attendance_df.empty or not site_guards:
        return 100.0, 0

    col_map = build_column_map(attendance_df)
    gid = col_map.get("guard_id")
    date_col = col_map.get("date")
    shift_col = col_map.get("shift")
    status_col = col_map.get("status")

    if not gid or not date_col:
        return 100.0, 0

    site_att = attendance_df[attendance_df[gid].astype(str).isin(site_guards)]
    if site_att.empty:
        return 50.0, 0

    missing_shifts = 0
    total_shifts = 0

    if shift_col and shift_col in site_att.columns:
        for date, day_group in site_att.groupby(date_col):
            shifts_covered = day_group[shift_col].nunique()
            expected = config.shifts_per_day
            total_shifts += expected
            if shifts_covered < expected:
                missing_shifts += expected - shifts_covered
    else:
        # Without shift data, check guard count per day
        for date, day_group in site_att.groupby(date_col):
            present = (day_group[status_col].astype(str).str.lower() == "present").sum() if status_col else len(day_group)
            total_shifts += 1
            if present < config.min_guards_per_shift:
                missing_shifts += 1

    if total_shifts == 0:
        return 100.0, 0

    coverage = ((total_shifts - missing_shifts) / total_shifts * 100)
    return round(max(coverage, 0), 2), missing_shifts


def understaffed_sites(
    assignments: pd.DataFrame,
    attendance_df: pd.DataFrame,
    config: SiteConfig,
) -> pd.DataFrame:
    """Find sites with insufficient guard coverage."""
    if assignments.empty:
        return pd.DataFrame()

    col_map = build_column_map(assignments)
    sid = col_map.get("site_id")
    if not sid:
        return pd.DataFrame()

    results = []
    for site_id in assignments[sid].dropna().unique():
        guards = get_site_guards(assignments, str(site_id))
        score, missing = calculate_shift_coverage(guards, attendance_df, config)
        if score < 80:
            results.append({
                "site_id": str(site_id),
                "guard_count": len(guards),
                "coverage_score": score,
                "missing_shifts": missing,
                "severity": "critical" if score < 50 else "high",
            })
    return pd.DataFrame(results) if results else pd.DataFrame()


# ============================================================
# MODULE 7 — GUARD UTILIZATION
# ============================================================


def calculate_guard_utilization(
    site_guards: List[str],
    attendance_df: pd.DataFrame,
) -> Tuple[float, int, int]:
    """Returns (utilization_score, idle_guards, overloaded_guards)."""
    if attendance_df.empty or not site_guards:
        return 100.0, 0, 0

    col_map = build_column_map(attendance_df)
    gid = col_map.get("guard_id")
    hours_col = col_map.get("hours_worked")
    status_col = col_map.get("status")

    if not gid:
        return 100.0, 0, 0

    site_att = attendance_df[attendance_df[gid].astype(str).isin(site_guards)]
    if site_att.empty:
        return 100.0, 0, 0

    idle = 0
    overloaded = 0

    if hours_col:
        guard_hours = site_att.groupby(gid)[hours_col].apply(
            lambda x: pd.to_numeric(x, errors="coerce").sum()
        )
        for guard, hours in guard_hours.items():
            if hours <= 0:
                idle += 1
            elif hours > 240:  # > 30 days × 8 hours
                overloaded += 1
    elif status_col:
        guard_attendance = site_att.groupby(gid)[status_col].apply(
            lambda x: (x.astype(str).str.lower() == "present").sum()
        )
        total_days = site_att[date_col].nunique() if (date_col := col_map.get("date")) else 30
        for guard, days in guard_attendance.items():
            pct = days / max(total_days, 1)
            if pct < 0.1:
                idle += 1
            elif pct > 1.0:
                overloaded += 1

    total = len(site_guards)
    balanced = total - idle - overloaded
    score = round((balanced / total * 100) if total else 100, 2)
    return max(score, 0), idle, overloaded


# ============================================================
# MODULE 3 — SITE RISK SCORING
# ============================================================


def calculate_site_risk(
    attendance_score: float,
    incident_score: float,
    complaint_score: float,
    compliance_score: float,
    total_incidents: int,
    high_incidents: int,
    total_complaints: int,
    absent_count: int,
    config: SiteConfig,
) -> Tuple[float, str]:
    """Composite risk score 0-100."""
    # Invert scores (high performance = low risk)
    att_risk = 100 - attendance_score
    inc_risk = 100 - incident_score
    comp_risk = 100 - complaint_score
    compl_risk = 100 - compliance_score

    risk = (
        att_risk * 0.30 +
        inc_risk * 0.25 +
        comp_risk * 0.20 +
        compl_risk * 0.15 +
        min(high_incidents * 5, 30) * 0.10
    )

    risk = min(max(risk, 0), 100)
    level = classify_risk(risk, config)
    return round(risk, 2), level


def calculate_risk_index(site_risk: float, guard_count: int) -> float:
    """Risk index adjusted for site size."""
    if guard_count <= 0:
        return site_risk
    size_factor = max(1.0 - guard_count * 0.01, 0.5)  # larger sites slightly lower risk
    return round(site_risk * size_factor, 2)


def classify_risk(score: float, config: SiteConfig) -> str:
    if score <= config.risk_safe:
        return RiskLevel.SAFE.value
    elif score <= config.risk_low:
        return RiskLevel.LOW.value
    elif score <= config.risk_medium:
        return RiskLevel.MEDIUM.value
    elif score <= config.risk_high:
        return RiskLevel.HIGH.value
    return RiskLevel.CRITICAL.value


# ============================================================
# MODULE 11 — AI SITE RANKING
# ============================================================


def rank_sites(performances: List[SitePerformance]) -> List[SitePerformance]:
    sorted_sites = sorted(performances, key=lambda s: s.performance_score, reverse=True)
    for i, s in enumerate(sorted_sites):
        s.rank = i + 1
    return sorted_sites


def detect_improvement(
    current: List[SitePerformance],
    previous: Dict[str, float],
) -> List[Dict[str, Any]]:
    """Detect most improved and most declined sites."""
    changes = []
    for sp in current:
        prev_score = previous.get(sp.site_id)
        if prev_score is not None:
            change = sp.performance_score - prev_score
            changes.append({
                "site_id": sp.site_id,
                "site_name": sp.site_name,
                "current_score": sp.performance_score,
                "previous_score": prev_score,
                "change": round(change, 2),
                "trend": "improved" if change > 2 else ("declined" if change < -2 else "stable"),
            })
    return sorted(changes, key=lambda x: x["change"], reverse=True)


# ============================================================
# MODULE 12 — ROOT CAUSE ANALYSIS
# ============================================================


def root_cause_analysis(sp: SitePerformance) -> List[str]:
    """Identify why a site is underperforming."""
    causes = []

    if sp.attendance_score < 70:
        causes.append(f"Low attendance ({sp.attendance_score:.0f}%) — absenteeism is high")
    if sp.incident_score < 70:
        causes.append(f"High incidents ({sp.total_incidents} total, {sp.high_incidents} high-severity)")
    if sp.complaint_score < 70:
        causes.append(f"Too many complaints ({sp.total_complaints}, {sp.unresolved_complaints} unresolved)")
    if sp.compliance_score < 70:
        causes.append(f"Compliance gaps ({sp.compliant_items}/{sp.compliance_items} items compliant)")
    if sp.shift_coverage_score < 70:
        causes.append(f"Shift gaps ({sp.missing_shifts} missing shifts)")
    if sp.guard_utilization_score < 70:
        causes.append(f"Poor utilization — {sp.idle_guards} idle, {sp.overloaded_guards} overloaded")

    if not causes and sp.performance_score < 60:
        causes.append("Multiple minor issues compounding across all KPIs")

    return causes


# ============================================================
# MODULE 13 — RECOMMENDATION ENGINE
# ============================================================


def recommend_site_actions(sp: SitePerformance, config: SiteConfig) -> List[str]:
    """Generate actionable recommendations."""
    recs = []

    if sp.attendance_score < 60:
        recs.append("Implement attendance monitoring. Deploy biometric systems. Conduct attendance counseling.")
    elif sp.attendance_score < 75:
        recs.append("Review attendance patterns. Address chronic absentees.")

    if sp.incident_score < 60:
        recs.append("Conduct incident investigation. Implement patrol frequency increase. Training on incident prevention.")
    elif sp.high_incidents > 3:
        recs.append("High-severity incidents detected — conduct site audit and supervisor review.")

    if sp.complaint_score < 60:
        recs.append("Address customer complaints immediately. Implement feedback loop. Replace underperforming guards.")

    if sp.compliance_score < 70:
        recs.append("Expedite compliance documentation. Schedule training. Verify PSARA license status.")

    if sp.shift_coverage_score < 70:
        recs.append(f"Deploy additional guards. {sp.missing_shifts} shifts need coverage.")

    if sp.idle_guards > 2:
        recs.append("Reassign idle guards to understaffed sites.")

    if sp.overloaded_guards > 2:
        recs.append("Reduce workload on overloaded guards. Add headcount.")

    if not recs:
        recs.append("Site performing well. Maintain current standards.")

    return recs


# ============================================================
# MODULE 14 — GEOGRAPHIC ANALYTICS
# ============================================================


def zone_performance(performances: List[SitePerformance]) -> pd.DataFrame:
    if not performances:
        return pd.DataFrame()

    zone_data: Dict[str, List[SitePerformance]] = defaultdict(list)
    for sp in performances:
        zone_data[sp.zone or "UNKNOWN"].append(sp)

    rows = []
    for zone, sites in zone_data.items():
        rows.append({
            "zone": zone,
            "site_count": len(sites),
            "total_guards": sum(s.guard_count for s in sites),
            "avg_performance": round(np.mean([s.performance_score for s in sites]), 2),
            "avg_risk": round(np.mean([s.risk_score for s in sites]), 2),
            "avg_attendance": round(np.mean([s.attendance_score for s in sites]), 2),
            "total_incidents": sum(s.total_incidents for s in sites),
            "total_complaints": sum(s.total_complaints for s in sites),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def district_summary(performances: List[SitePerformance]) -> pd.DataFrame:
    if not performances:
        return pd.DataFrame()

    dist_data: Dict[str, List[SitePerformance]] = defaultdict(list)
    for sp in performances:
        dist_data[sp.district or "UNKNOWN"].append(sp)

    rows = []
    for district, sites in dist_data.items():
        rows.append({
            "district": district,
            "site_count": len(sites),
            "avg_performance": round(np.mean([s.performance_score for s in sites]), 2),
            "best_site": max(sites, key=lambda s: s.performance_score).site_id,
            "worst_site": min(sites, key=lambda s: s.performance_score).site_id,
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ============================================================
# MODULE 15 — SUPERVISOR PERFORMANCE
# ============================================================


def calculate_supervisor_score(
    performances: List[SitePerformance],
) -> pd.DataFrame:
    if not performances:
        return pd.DataFrame()

    sup_data: Dict[str, List[SitePerformance]] = defaultdict(list)
    for sp in performances:
        sup_data[sp.supervisor or "UNKNOWN"].append(sp)

    rows = []
    for sup, sites in sup_data.items():
        rows.append({
            "supervisor": sup,
            "sites_managed": len(sites),
            "total_guards": sum(s.guard_count for s in sites),
            "avg_performance": round(np.mean([s.performance_score for s in sites]), 2),
            "avg_attendance": round(np.mean([s.attendance_score for s in sites]), 2),
            "total_incidents": sum(s.total_incidents for s in sites),
            "total_complaints": sum(s.total_complaints for s in sites),
            "grade": assign_grade(np.mean([s.performance_score for s in sites])),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def rank_supervisors(performances: List[SitePerformance]) -> pd.DataFrame:
    df = calculate_supervisor_score(performances)
    if df.empty:
        return df
    df = df.sort_values("avg_performance", ascending=False).reset_index(drop=True)
    df["rank"] = range(1, len(df) + 1)
    return df


# ============================================================
# MODULE 16 — AI PREDICTION
# ============================================================


def predict_next_month_score(
    current_score: float,
    trend_data: List[float],
) -> Dict[str, float]:
    """Simple linear trend prediction."""
    if len(trend_data) < 2:
        return {"predicted": current_score, "confidence": 50.0}

    # Simple linear regression on trend data
    x = np.arange(len(trend_data))
    y = np.array(trend_data)
    if len(x) < 2:
        return {"predicted": current_score, "confidence": 50.0}

    slope = np.polyfit(x, y, 1)[0]
    predicted = round(current_score + slope, 2)
    predicted = max(0, min(100, predicted))

    # Confidence based on trend consistency
    diffs = np.diff(trend_data)
    if len(diffs) > 0:
        consistency = 1.0 - (np.std(diffs) / max(np.mean(np.abs(diffs)), 1))
        confidence = round(max(min(consistency * 100, 95), 30), 1)
    else:
        confidence = 50.0

    return {"predicted": predicted, "confidence": confidence}


# ============================================================
# MODULE 17 — SITE BENCHMARKING
# ============================================================


def benchmark_sites(
    performances: List[SitePerformance],
) -> pd.DataFrame:
    """Compare all sites against benchmarks."""
    if not performances:
        return pd.DataFrame()

    avg_perf = np.mean([s.performance_score for s in performances])
    avg_att = np.mean([s.attendance_score for s in performances])
    avg_inc = np.mean([s.incident_score for s in performances])

    rows = []
    for sp in performances:
        rows.append({
            "site_id": sp.site_id,
            "site_name": sp.site_name,
            "performance_score": sp.performance_score,
            "vs_avg_performance": round(sp.performance_score - avg_perf, 2),
            "attendance_score": sp.attendance_score,
            "vs_avg_attendance": round(sp.attendance_score - avg_att, 2),
            "incident_score": sp.incident_score,
            "vs_avg_incident": round(sp.incident_score - avg_inc, 2),
            "grade": sp.grade,
            "benchmark_status": "above" if sp.performance_score > avg_perf else "below",
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ============================================================
# MODULE 2 — MULTI-MONTH TREND
# ============================================================


def calculate_monthly_score(
    sources: Dict[str, pd.DataFrame],
    config: SiteConfig,
    month_label: str = "",
) -> List[SitePerformance]:
    """Calculate scores for one month of data."""
    assignments = sources.get("assignments", pd.DataFrame())
    attendance = sources.get("attendance", pd.DataFrame())
    incidents = sources.get("incidents", pd.DataFrame())
    complaints = sources.get("complaints", pd.DataFrame())
    compliance = sources.get("compliance", pd.DataFrame())

    if assignments.empty:
        logger.warning("No site assignments data")
        return []

    col_map = build_column_map(assignments)
    sid = col_map.get("site_id")
    sname = col_map.get("site_name")
    client_col = col_map.get("client")
    zone_col = col_map.get("zone")
    dist_col = col_map.get("district")
    city_col = col_map.get("city")
    sup_col = col_map.get("supervisor")

    if not sid:
        logger.error("No site_id column found in assignments")
        return []

    performances = []

    for site_id in assignments[sid].dropna().unique():
        site_id_str = str(site_id).strip()
        site_df = assignments[assignments[sid].astype(str).str.strip() == site_id_str]
        guards = [str(g) for g in site_df[col_map.get("guard_id", "Guard_ID")].dropna().tolist()] if col_map.get("guard_id") else []

        # Site metadata
        site_name = str(site_df.iloc[0].get(sname, site_id_str)) if sname and not site_df.empty else site_id_str
        client = str(site_df.iloc[0].get(client_col, "")) if client_col and not site_df.empty else ""
        zone = str(site_df.iloc[0].get(zone_col, "")) if zone_col and not site_df.empty else ""
        district = str(site_df.iloc[0].get(dist_col, "")) if dist_col and not site_df.empty else ""
        city = str(site_df.iloc[0].get(city_col, "")) if city_col and not site_df.empty else ""
        supervisor = str(site_df.iloc[0].get(sup_col, "")) if sup_col and not site_df.empty else ""

        # Score all dimensions
        att_score, att_total, att_present, att_absent = calculate_attendance_score(guards, attendance)
        inc_score, inc_total, inc_high = calculate_incident_score(guards, incidents, config)
        comp_score, comp_total, comp_unresolved = calculate_complaint_score(guards, complaints, config)
        compl_score, compl_total, compl_compliant = calculate_compliance_score(guards, compliance)
        shift_score, missing_shifts = calculate_shift_coverage(guards, attendance, config)
        util_score, idle, overloaded = calculate_guard_utilization(guards, attendance)
        sla_score = calculate_sla_score(guards, incidents, complaints, config)

        # Final performance score
        final = round(
            att_score * config.weight_attendance +
            inc_score * config.weight_incident +
            comp_score * config.weight_complaint +
            compl_score * config.weight_compliance +
            shift_score * config.weight_shift_coverage +
            util_score * config.weight_guard_utilization,
            2,
        )

        grade = assign_grade(final)

        # Risk
        risk_score, risk_level = calculate_site_risk(
            att_score, inc_score, comp_score, compl_score,
            inc_total, inc_high, comp_total, att_absent, config,
        )

        sp = SitePerformance(
            site_id=site_id_str,
            site_name=site_name,
            client=client,
            zone=zone,
            district=district,
            city=city,
            supervisor=supervisor,
            guard_count=len(guards),
            month=month_label,
            attendance_score=att_score,
            incident_score=inc_score,
            complaint_score=comp_score,
            compliance_score=compl_score,
            shift_coverage_score=shift_score,
            guard_utilization_score=util_score,
            sla_score=sla_score,
            performance_score=final,
            risk_score=risk_score,
            grade=grade,
            risk_level=risk_level,
            total_attendance=att_total,
            present_count=att_present,
            absent_count=att_absent,
            total_incidents=inc_total,
            high_incidents=inc_high,
            total_complaints=comp_total,
            unresolved_complaints=comp_unresolved,
            compliance_items=compl_total,
            compliant_items=compl_compliant,
            missing_shifts=missing_shifts,
            idle_guards=idle,
            overloaded_guards=overloaded,
        )

        # Root cause & recommendations
        sp.root_causes = root_cause_analysis(sp)
        sp.recommendations = recommend_site_actions(sp, config)

        performances.append(sp)

    return performances


def calculate_site_trend(
    monthly_scores: Dict[str, List[SitePerformance]],
) -> pd.DataFrame:
    """Track site performance across months."""
    rows = []
    for month_key in sorted(monthly_scores.keys()):
        for sp in monthly_scores[month_key]:
            rows.append({
                "month": month_key,
                "site_id": sp.site_id,
                "site_name": sp.site_name,
                "performance_score": sp.performance_score,
                "risk_score": sp.risk_score,
                "grade": sp.grade,
                "attendance_score": sp.attendance_score,
                "incident_score": sp.incident_score,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Add trend per site
    if len(monthly_scores) >= 2:
        trends = []
        for site_id in df["site_id"].unique():
            site_df = df[df["site_id"] == site_id].sort_values("month")
            if len(site_df) >= 2:
                latest = site_df.iloc[-1]["performance_score"]
                prev = site_df.iloc[-2]["performance_score"]
                change = latest - prev
                trend = "improving" if change > 2 else ("declining" if change < -2 else "stable")
            else:
                trend = "baseline"
            for _, row in site_df.iterrows():
                trends.append(trend)
        df["trend"] = trends

    return df


def detect_score_drop(
    current: List[SitePerformance],
    previous: Dict[str, float],
    threshold: float = 10.0,
) -> pd.DataFrame:
    """Detect sites with significant score drops."""
    drops = []
    for sp in current:
        prev = previous.get(sp.site_id)
        if prev is not None:
            drop = prev - sp.performance_score
            if drop > threshold:
                drops.append({
                    "site_id": sp.site_id,
                    "site_name": sp.site_name,
                    "current_score": sp.performance_score,
                    "previous_score": prev,
                    "drop": round(drop, 2),
                    "severity": "critical" if drop > 20 else "high",
                })
    return pd.DataFrame(drops) if drops else pd.DataFrame()


def compare_previous_month(
    current: List[SitePerformance],
    previous_month_data: Optional[Path] = None,
) -> Dict[str, Any]:
    if previous_month_data is None or not previous_month_data.exists():
        return {"status": "no_previous_data"}
    prev_df = pd.read_csv(previous_month_data)
    if prev_df.empty:
        return {"status": "no_previous_data"}

    prev_lookup = {}
    if "site_id" in prev_df.columns and "performance_score" in prev_df.columns:
        for _, row in prev_df.iterrows():
            prev_lookup[str(row["site_id"])] = float(row["performance_score"])

    improved = sum(1 for sp in current if sp.performance_score > prev_lookup.get(sp.site_id, 0) + 2)
    declined = sum(1 for sp in current if sp.performance_score < prev_lookup.get(sp.site_id, 0) - 2)
    stable = len(current) - improved - declined

    return {"improved": improved, "declined": declined, "stable": stable}


# ============================================================
# FINAL SCORE & GRADE
# ============================================================


def calculate_final_score(
    attendance_score: float,
    incident_score: float,
    complaint_score: float,
    compliance_score: float,
    shift_score: float = 100.0,
    util_score: float = 100.0,
    config: Optional[SiteConfig] = None,
) -> float:
    cfg = config or SiteConfig()
    return round(
        attendance_score * cfg.weight_attendance +
        incident_score * cfg.weight_incident +
        complaint_score * cfg.weight_complaint +
        compliance_score * cfg.weight_compliance +
        shift_score * cfg.weight_shift_coverage +
        util_score * cfg.weight_guard_utilization,
        2,
    )


def assign_grade(score: float) -> str:
    if score >= 90:
        return Grade.EXCELLENT.value
    elif score >= 75:
        return Grade.GOOD.value
    elif score >= 60:
        return Grade.AVERAGE.value
    elif score >= 40:
        return Grade.POOR.value
    return Grade.CRITICAL.value


# ============================================================
# MODULE 4 — KPI DASHBOARD
# ============================================================


def build_dashboard(
    performances: List[SitePerformance],
    config: SiteConfig,
) -> Dict[str, Any]:
    if not performances:
        return {}

    scores = [s.performance_score for s in performances]
    grades = [s.grade for s in performances]
    grade_dist = defaultdict(int)
    for g in grades:
        grade_dist[g] += 1

    best = max(performances, key=lambda s: s.performance_score)
    worst = min(performances, key=lambda s: s.performance_score)

    return {
        "generated_at": datetime.now().isoformat(),
        "engine_version": config.engine_version,
        "summary": {
            "total_sites": len(performances),
            "total_guards": sum(s.guard_count for s in performances),
            "avg_score": round(float(np.mean(scores)), 2),
            "median_score": round(float(np.median(scores)), 2),
            "std_score": round(float(np.std(scores)), 2),
            "best_site": {"id": best.site_id, "name": best.site_name, "score": best.performance_score},
            "worst_site": {"id": worst.site_id, "name": worst.site_name, "score": worst.performance_score},
        },
        "grade_distribution": dict(grade_dist),
        "kpi_averages": {
            "attendance": round(float(np.mean([s.attendance_score for s in performances])), 2),
            "incidents": round(float(np.mean([s.incident_score for s in performances])), 2),
            "complaints": round(float(np.mean([s.complaint_score for s in performances])), 2),
            "compliance": round(float(np.mean([s.compliance_score for s in performances])), 2),
            "shift_coverage": round(float(np.mean([s.shift_coverage_score for s in performances])), 2),
            "utilization": round(float(np.mean([s.guard_utilization_score for s in performances])), 2),
        },
        "risk_distribution": {
            level.value: sum(1 for s in performances if s.risk_level == level.value)
            for level in RiskLevel
        },
        "high_risk_count": sum(1 for s in performances if s.risk_level in ("high", "critical")),
    }


# ============================================================
# MODULE 20 — EXECUTIVE SUMMARY
# ============================================================


def generate_executive_summary(
    performances: List[SitePerformance],
    config: SiteConfig,
) -> Dict[str, Any]:
    if not performances:
        return {}

    dashboard = build_dashboard(performances, config)
    top_10 = sorted(performances, key=lambda s: s.performance_score, reverse=True)[:10]
    bottom_10 = sorted(performances, key=lambda s: s.performance_score)[:10]
    high_risk = [s for s in performances if s.risk_level in ("high", "critical")]

    # Collect all recommendations
    all_recs = []
    for sp in performances:
        all_recs.extend(sp.recommendations)
    rec_freq = defaultdict(int)
    for r in all_recs:
        rec_freq[r[:80]] += 1

    return {
        **dashboard,
        "top_10_sites": [
            {"site": s.site_id, "name": s.site_name, "score": s.performance_score, "grade": s.grade}
            for s in top_10
        ],
        "bottom_10_sites": [
            {"site": s.site_id, "name": s.site_name, "score": s.performance_score, "grade": s.grade,
             "root_causes": s.root_causes[:2]}
            for s in bottom_10
        ],
        "high_risk_sites": [
            {"site": s.site_id, "risk_score": s.risk_score, "risk_level": s.risk_level}
            for s in sorted(high_risk, key=lambda s: s.risk_score, reverse=True)[:10]
        ],
        "top_recommendations": sorted(rec_freq.items(), key=lambda x: x[1], reverse=True)[:10],
    }


# ============================================================
# MODULE 21 — ML READINESS
# ============================================================


def build_ml_features(performances: List[SitePerformance]) -> pd.DataFrame:
    """Engineer features for future ML models."""
    rows = []
    for sp in performances:
        rows.append({
            "site_id": sp.site_id,
            "guard_count": sp.guard_count,
            "attendance_pct": sp.attendance_score,
            "incident_rate": round(sp.total_incidents / max(sp.guard_count, 1), 2),
            "complaint_rate": round(sp.total_complaints / max(sp.guard_count, 1), 2),
            "compliance_pct": sp.compliance_score,
            "shift_coverage_pct": sp.shift_coverage_score,
            "guard_utilization_pct": sp.guard_utilization_score,
            "absenteeism_rate": round(sp.absent_count / max(sp.total_attendance, 1) * 100, 2),
            "high_incident_rate": round(sp.high_incidents / max(sp.total_incidents, 1) * 100, 2),
            "unresolved_complaint_rate": round(sp.unresolved_complaints / max(sp.total_complaints, 1) * 100, 2),
            "sla_score": sp.sla_score,
            "performance_score": sp.performance_score,
            "risk_score": sp.risk_score,
            "grade_encoded": {"Excellent": 4, "Good": 3, "Average": 2, "Poor": 1, "Critical": 0}.get(sp.grade, 0),
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ============================================================
# EXPORT FUNCTIONS
# ============================================================


def export_csv(reports: Dict[str, pd.DataFrame]):
    for name, df in reports.items():
        if df is not None and not df.empty:
            path = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(path, index=False, encoding="utf-8-sig")
            logger.info(f"CSV → {path} ({len(df)} rows)")


def export_excel(reports: Dict[str, pd.DataFrame]):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"site_performance_{ts}.xlsx"
    sheets = {k[:31]: v for k, v in reports.items() if v is not None and not v.empty}
    if not sheets:
        return
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sn, df in sheets.items():
            df.to_excel(writer, sheet_name=sn, index=False)
    logger.info(f"Excel → {path} ({len(sheets)} sheets)")


def export_json(dashboard: Dict, exec_summary: Dict, stats: RuntimeStats):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {**dashboard, "executive_summary": exec_summary, "runtime_stats": stats.summary()}
    path = SUMMARY_DIR / f"site_performance_summary_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"JSON → {path}")


def export_dashboard_json(dashboard: Dict, exec_summary: Dict):
    """Export dashboard-ready JSON for frontend consumption."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = {
        "dashboard": SUMMARY_DIR / f"dashboard_{ts}.json",
        "site_summary": SUMMARY_DIR / f"site_summary_{ts}.json",
    }
    for key, path in paths.items():
        data = dashboard if key == "dashboard" else exec_summary
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"JSON → {path}")


# ============================================================
# BUILD SITE PERFORMANCE (backward-compatible)
# ============================================================


def build_site_performance(
    sources: Optional[Dict[str, pd.DataFrame]] = None,
    config: Optional[SiteConfig] = None,
) -> pd.DataFrame:
    """Backward-compatible function."""
    cfg = config or SiteConfig()
    if sources is None:
        sources = load_data()

    performances = calculate_monthly_score(sources, cfg)
    if not performances:
        return pd.DataFrame()

    performances = rank_sites(performances)

    rows = []
    for sp in performances:
        rows.append({
            "Site_ID": sp.site_id,
            "Site_Name": sp.site_name,
            "Client": sp.client,
            "Zone": sp.zone,
            "Guard_Count": sp.guard_count,
            "Attendance_Score": sp.attendance_score,
            "Incident_Score": sp.incident_score,
            "Complaint_Score": sp.complaint_score,
            "Compliance_Score": sp.compliance_score,
            "Shift_Coverage_Score": sp.shift_coverage_score,
            "Utilization_Score": sp.guard_utilization_score,
            "SLA_Score": sp.sla_score,
            "Final_Score": sp.performance_score,
            "Risk_Score": sp.risk_score,
            "Grade": sp.grade,
            "Risk_Level": sp.risk_level,
            "Rank": sp.rank,
            "Root_Causes": "; ".join(sp.root_causes[:3]),
            "Recommendations": "; ".join(sp.recommendations[:3]),
        })
    return pd.DataFrame(rows)


# ============================================================
# MAIN ENGINE
# ============================================================


class SitePerformanceEngine:
    """
    Production site performance scoring engine.
    Runs all 21 modules.
    """

    def __init__(
        self,
        config: Optional[SiteConfig] = None,
        client: str = "default",
        month: str = "",
    ):
        self.config = config or load_config()
        self.client = client
        self.month = month
        self.stats = RuntimeStats()

        self.sources: Dict[str, pd.DataFrame] = {}
        self.performances: List[SitePerformance] = []
        self.dashboard: Dict[str, Any] = {}
        self.executive_summary: Dict[str, Any] = {}

        _audit_log.clear()

    def run(self) -> Dict[str, Any]:
        self.stats = RuntimeStats()
        cfg = self.config

        logger.info("=" * 70)
        logger.info("SITE PERFORMANCE SCORING ENGINE")
        logger.info(f"Engine version: {cfg.engine_version}")
        logger.info(f"Client: {self.client}, Month: {self.month or 'current'}")
        logger.info("=" * 70)

        # ── 1. Load data ──
        logger.info("PHASE 1: LOADING DATA")
        self.sources = load_client_data(self.client, self.month)
        self.stats.files_loaded = len(self.sources)
        for k, df in self.sources.items():
            self.stats.rows_loaded += len(df)
        audit_log("ENGINE_START", "loader", f"Client={self.client}, Sources={len(self.sources)}")

        # ── 2. Calculate monthly scores ──
        logger.info("PHASE 2: SCORING ALL SITES")
        self.performances = calculate_monthly_score(
            self.sources, cfg, self.month or datetime.now().strftime("%Y-%m")
        )
        self.stats.sites_scored = len(self.performances)
        logger.info(f"Sites scored: {len(self.performances)}")

        if not self.performances:
            logger.error("No sites scored — check input data")
            self.stats.finish()
            return {"error": "No sites scored"}

        # ── 3. Rank sites ──
        logger.info("PHASE 3: RANKING")
        self.performances = rank_sites(self.performances)

        # ── 4. Previous month comparison ──
        logger.info("PHASE 4: TREND ANALYSIS")
        prev_file = OUTPUT_DIR / "site_performance_scores.csv"
        comparison = compare_previous_month(self.performances, prev_file)
        prev_scores = {}
        if prev_file.exists():
            try:
                prev_df = pd.read_csv(prev_file)
                if "Site_ID" in prev_df.columns and "Final_Score" in prev_df.columns:
                    prev_scores = dict(zip(prev_df["Site_ID"].astype(str), prev_df["Final_Score"]))
            except Exception:
                pass

        improvements = detect_improvement(self.performances, prev_scores)
        drops = detect_score_drop(self.performances, prev_scores)

        # ── 5. Incident analytics ──
        logger.info("PHASE 5: INCIDENT ANALYTICS")
        inc_summary = incident_summary(self.sources.get("incidents", pd.DataFrame()))
        repeat_incidents = repeat_incident_detection(self.sources.get("incidents", pd.DataFrame()))

        # ── 6. Complaint analytics ──
        logger.info("PHASE 6: COMPLAINT ANALYTICS")
        comp_summary = complaint_summary(self.sources.get("complaints", pd.DataFrame()))

        # ── 7. Shift coverage ──
        logger.info("PHASE 7: SHIFT COVERAGE")
        understaffed = understaffed_sites(
            self.sources.get("assignments", pd.DataFrame()),
            self.sources.get("attendance", pd.DataFrame()),
            cfg,
        )

        # ── 8. Geographic analytics ──
        logger.info("PHASE 8: GEOGRAPHIC ANALYTICS")
        zone_df = zone_performance(self.performances)
        district_df = district_summary(self.performances)

        # ── 9. Supervisor performance ──
        logger.info("PHASE 9: SUPERVISOR PERFORMANCE")
        sup_ranking = rank_supervisors(self.performances)

        # ── 10. Benchmarking ──
        logger.info("PHASE 10: BENCHMARKING")
        benchmarks = benchmark_sites(self.performances)

        # ── 11. Dashboard & Summary ──
        logger.info("PHASE 11: DASHBOARD")
        self.dashboard = build_dashboard(self.performances, cfg)
        self.executive_summary = generate_executive_summary(self.performances, cfg)

        # ── 12. ML features ──
        logger.info("PHASE 12: ML FEATURES")
        ml_features = build_ml_features(self.performances)

        # ── 13. Export ──
        logger.info("PHASE 13: EXPORT")
        self.stats.finish()
        audit_log("ENGINE_COMPLETE", "all", f"Elapsed={self.stats.elapsed}s")

        # Build main report
        main_df = build_site_performance(self.sources, cfg)

        # Build per-site detail
        detail_rows = []
        for sp in self.performances:
            detail_rows.append(asdict(sp))
        detail_df = pd.DataFrame(detail_rows) if detail_rows else pd.DataFrame()

        all_reports = {
            "site_performance_scores": main_df,
            "site_performance_detail": detail_df,
            "site_rankings": benchmarks,
            "zone_performance": zone_df,
            "district_summary": district_df,
            "supervisor_ranking": sup_ranking,
            "understaffed_sites": understaffed,
            "improvement_analysis": pd.DataFrame(improvements) if improvements else pd.DataFrame(),
            "score_drops": drops,
            "repeat_incidents": repeat_incidents,
            "incident_summary": pd.DataFrame([inc_summary]) if inc_summary else pd.DataFrame(),
            "complaint_summary": pd.DataFrame([comp_summary]) if comp_summary else pd.DataFrame(),
            "ml_features": ml_features,
            "audit_trail": get_audit_dataframe(),
        }

        csv_reports = {k: v for k, v in all_reports.items() if v is not None and not v.empty}
        export_csv(csv_reports)
        export_excel(csv_reports)
        export_json(self.dashboard, self.executive_summary, self.stats)
        export_dashboard_json(self.dashboard, self.executive_summary)

        # ── Final summary ──
        logger.info("=" * 70)
        logger.info("SITE PERFORMANCE SCORING COMPLETE")
        logger.info(f"  Elapsed:          {self.stats.elapsed}s")
        logger.info(f"  Files loaded:     {self.stats.files_loaded}")
        logger.info(f"  Sites scored:     {self.stats.sites_scored}")
        logger.info(f"  Avg performance:  {self.dashboard.get('summary', {}).get('avg_score', 0)}")
        logger.info(f"  Best site:        {self.dashboard.get('summary', {}).get('best_site', {}).get('id', '')}")
        logger.info(f"  Worst site:       {self.dashboard.get('summary', {}).get('worst_site', {}).get('id', '')}")
        logger.info(f"  High risk sites:  {self.dashboard.get('high_risk_count', 0)}")
        logger.info(f"  CSV files:        {len(csv_reports)}")
        logger.info("=" * 70)

        return {**self.dashboard, "executive_summary": self.executive_summary}


# ============================================================
# BACKWARD-COMPATIBLE run()
# ============================================================


def run():
    engine = SitePerformanceEngine()
    return engine.run()


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Site Performance Scoring Engine")
    parser.add_argument("--client", default="default", help="Client name")
    parser.add_argument("--month", default="", help="Month folder name")
    parser.add_argument("--config", default=None, help="Config file path")
    parser.add_argument("--list-clients", action="store_true", help="List available clients")

    args = parser.parse_args()

    if args.list_clients:
        clients = list_available_clients()
        print(f"Available clients: {clients}")
        for c in clients:
            months = list_available_months(c)
            print(f"  {c}: {months}")
        sys.exit(0)

    cfg = load_config(Path(args.config) if args.config else None)
    engine = SitePerformanceEngine(config=cfg, client=args.client, month=args.month)
    result = engine.run()
    print(json.dumps(result, indent=2, default=str))
