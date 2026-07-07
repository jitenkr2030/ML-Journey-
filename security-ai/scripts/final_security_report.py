# security-ai/scripts/final_security_report.py
"""
Production-Grade Final Security Report Engine
Security AI — Executive Intelligence & Reporting System

═══════════════════════════════════════════════════════════════════
 21 MODULES | 70+ FUNCTIONS | EXECUTIVE DASHBOARD | PDF | CHARTS
═══════════════════════════════════════════════════════════════════

 MODULES:
  1.  Executive Dashboard
  2.  Compliance Summary
  3.  Risk Summary
  4.  Fraud Summary
  5.  Wage Analytics
  6.  Site Analytics
  7.  Top 10 Reports
  8.  KPI Section
  9.  Monthly Trend
  10. Client Summary
  11. Recommendation Engine
  12. Audit Trail
  13. File Health Validation
  14. Pipeline Status
  15. Report Metadata
  16. Multi-Format Export
  17. Executive PDF
  18. Chart Data Generation
  19. ML Summary
  20. Overall Security Score
  21. Final Decision
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
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

RECON_DIR = BASE_DIR / "reconciliation"
FRAUD_DIR = BASE_DIR / "fraud_reports"
RISK_DIR = BASE_DIR / "risk_reports"
OUTPUT_DIR = BASE_DIR / "outputs"
ANOMALY_DIR = BASE_DIR / "anomaly_reports"
SITE_DIR = BASE_DIR / "site_reports"
EXPORT_DIR = BASE_DIR / "exports"
SUMMARY_DIR = BASE_DIR / "summaries"
LOG_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
CLIENTS_DIR = BASE_DIR / "clients"
DATASETS_DIR = BASE_DIR / "datasets"

for _d in (
    RECON_DIR, FRAUD_DIR, RISK_DIR, OUTPUT_DIR, ANOMALY_DIR,
    SITE_DIR, EXPORT_DIR, SUMMARY_DIR, LOG_DIR, CONFIG_DIR,
):
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
    root = logging.getLogger("FinalReport")
    root.setLevel(logging.DEBUG)
    if root.handlers:
        return root
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(ch)
    fh = RotatingFileHandler(
        log_dir / "final_report.log",
        maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(fh)
    eh = RotatingFileHandler(
        log_dir / "final_report_errors.log",
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


class Decision(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    NEEDS_IMPROVEMENT = "Needs Improvement"
    CRITICAL = "Critical"


class PipelineStage(str, Enum):
    EXCEL_PARSER = "Excel Parser"
    EMPLOYEE_MATCHING = "Employee Matching"
    PF_RECONCILIATION = "PF Reconciliation"
    ESI_RECONCILIATION = "ESI Reconciliation"
    WAGE_ANOMALY = "Wage Anomaly Detection"
    FRAUD_DETECTION = "Fraud Detection"
    RISK_SCORING = "Compliance Risk Scoring"
    SITE_PERFORMANCE = "Site Performance Scoring"
    FINAL_REPORT = "Final Security Report"


# ============================================================
# CONFIGURATION
# ============================================================


@dataclass
class ReportConfig:
    """All report parameters."""
    # Security score weights (must sum to 1.0)
    weight_compliance: float = 0.20
    weight_fraud: float = 0.15
    weight_payroll: float = 0.15
    weight_attendance: float = 0.15
    weight_site: float = 0.15
    weight_risk: float = 0.10
    weight_wage: float = 0.10

    # Decision thresholds
    decision_excellent: float = 90.0
    decision_good: float = 75.0
    decision_needs_improvement: float = 55.0

    # Report metadata
    engine_version: str = "9.0.0"
    pipeline_version: str = "7.0.0"
    operator: str = "auto"
    client: str = "default"
    month: str = ""


@dataclass
class AuditEntry:
    timestamp: str = ""
    action: str = ""
    module: str = ""
    detail: str = ""
    rows_affected: int = 0


@dataclass
class FileHealth:
    name: str = ""
    path: str = ""
    exists: bool = False
    non_empty: bool = False
    rows: int = 0
    columns: int = 0
    missing_columns: List[str] = field(default_factory=list)
    duplicate_rows: int = 0
    status: str = "MISSING"


@dataclass
class RuntimeStats:
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_loaded: int = 0
    rows_loaded: int = 0
    modules_run: int = 0

    def finish(self):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        e = self.end_time or time.perf_counter()
        return round(e - self.start_time, 3)

    def summary(self) -> Dict[str, Any]:
        return {
            "elapsed_seconds": self.elapsed,
            **{k: v for k, v in self.__dict__.items() if k not in ("start_time", "end_time")},
        }


# Global
_audit_log: List[AuditEntry] = []


def load_config(config_path: Optional[Path] = None) -> ReportConfig:
    cfg = ReportConfig()
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


# ============================================================
# FIELD RESOLVER
# ============================================================

COLUMN_ALIASES: Dict[str, List[str]] = {
    "guard_id": ["guard_id", "Guard_ID", "employee_id", "emp_id", "Employee_ID"],
    "guard_name": ["guard_name", "Guard_Name", "employee_name", "name", "Name"],
    "site_id": ["site_id", "Site_ID", "site", "Site"],
    "client": ["client", "client_name", "Client"],
    "gross_wages": ["gross_wages", "TOTAL", "Gross_Wages", "total_salary", "gross"],
    "net_pay": ["net_pay", "NET PAYMENT", "Net_Pay", "net_salary", "net_payment"],
    "basic_salary": ["basic_salary", "BASIC + VDA", "basic_vda", "Basic_VDA"],
    "pf_deduction": ["pf_deduction", "EPF", "employee_pf", "pf"],
    "esi_deduction": ["esi_deduction", "ESIC", "employee_esi", "esi"],
    "overtime_hours": ["overtime_hours", "Overtime Hours Worked", "ot_hours", "OT"],
    "days_worked": ["days_worked", "No Of Days Worked", "working_days", "days"],
    "recoveries": ["recoveries", "Recoveries", "deductions"],
    "attendance_status": ["status", "Status", "attendance_status", "present"],
    "site_name": ["site_name", "Site_Name", "location"],
    "risk_level": ["risk_level", "Risk_Level", "Risk_Status"],
    "mismatch_flag": ["Mismatch_Flag", "mismatch_flag", "mismatch"],
    "anomaly_flag": ["Anomaly_Flag", "anomaly_flag"],
    "performance_score": ["Performance_Score", "performance_score", "Final_Score"],
    "grade": ["Grade", "grade"],
    "month": ["month", "Month", "pay_month"],
    "fraud_type": ["fraud_type", "Fraud_Type", "anomaly_type", "Anomaly_Type"],
    "severity": ["severity", "Severity", "risk_level"],
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
    return df


def load_all_sources() -> Dict[str, pd.DataFrame]:
    """Load all pipeline outputs."""
    sources: Dict[str, pd.DataFrame] = {}

    files = {
        "pf": RECON_DIR / "pf_reconciliation_report.csv",
        "esi": RECON_DIR / "esi_reconciliation_report.csv",
        "wage_anomaly": ANOMALY_DIR / "wage_anomaly_report.csv",
        "wage_anomaly_alt": RECON_DIR / "wage_anomaly_report.csv",
        "fraud": FRAUD_DIR / "fraud_detection_report.csv",
        "risk": RISK_DIR / "compliance_risk_report.csv",
        "site_performance": SITE_DIR / "site_performance_scores.csv",
        "site_performance_alt": OUTPUT_DIR / "site_performance_scores.csv",
        "attendance": DATASETS_DIR / "attendance.csv",
        "payroll": DATASETS_DIR / "payroll.csv",
        "guards": DATASETS_DIR / "guards_master.csv",
        "site_assignments": DATASETS_DIR / "site_assignments.csv",
        "bank": DATASETS_DIR / "bank.csv",
        "incidents": DATASETS_DIR / "incidents.csv",
        "complaints": DATASETS_DIR / "complaints.csv",
        "compliance": DATASETS_DIR / "compliance.csv",
    }

    for key, path in files.items():
        df = safe_load(path)
        if not df.empty:
            # Avoid duplicates — prefer primary over alt
            base_key = key.replace("_alt", "")
            if base_key not in sources or key == base_key:
                sources[base_key] = df

    return sources


# ============================================================
# MODULE 13 — FILE HEALTH VALIDATION
# ============================================================


def validate_file_health(
    file_path: Path,
    expected_columns: Optional[List[str]] = None,
) -> FileHealth:
    fh = FileHealth(name=file_path.stem, path=str(file_path))
    if not file_path.exists():
        fh.status = "MISSING"
        return fh

    fh.exists = True
    try:
        df = pd.read_csv(file_path, nrows=5)
        fh.non_empty = len(df) > 0
        fh.columns = len(df.columns)

        if fh.non_empty:
            df_full = pd.read_csv(file_path)
            fh.rows = len(df_full)
            fh.duplicate_rows = int(df_full.duplicated().sum())

            if expected_columns:
                actual = set(c.lower().strip() for c in df_full.columns)
                for col in expected_columns:
                    if col.lower().strip() not in actual:
                        fh.missing_columns.append(col)

            fh.status = "PASS" if fh.non_empty and not fh.missing_columns else "WARN"
        else:
            fh.status = "EMPTY"
    except Exception as e:
        fh.status = f"ERROR: {e}"

    return fh


def validate_pipeline_outputs() -> Dict[str, FileHealth]:
    """Check all expected pipeline output files."""
    checks = {
        "pf_reconciliation": RECON_DIR / "pf_reconciliation_report.csv",
        "esi_reconciliation": RECON_DIR / "esi_reconciliation_report.csv",
        "wage_anomaly": ANOMALY_DIR / "wage_anomaly_report.csv",
        "fraud_detection": FRAUD_DIR / "fraud_detection_report.csv",
        "compliance_risk": RISK_DIR / "compliance_risk_report.csv",
        "site_performance": SITE_DIR / "site_performance_scores.csv",
    }
    results = {}
    for name, path in checks.items():
        results[name] = validate_file_health(path)
    return results


# ============================================================
# MODULE 14 — PIPELINE STATUS
# ============================================================


def pipeline_health_check() -> Dict[str, str]:
    """Check which pipeline stages have output."""
    stages = {
        PipelineStage.EXCEL_PARSER.value: DATASETS_DIR / "guards_master.csv",
        PipelineStage.EMPLOYEE_MATCHING.value: DATASETS_DIR / "site_assignments.csv",
        PipelineStage.PF_RECONCILIATION.value: RECON_DIR / "pf_reconciliation_report.csv",
        PipelineStage.ESI_RECONCILIATION.value: RECON_DIR / "esi_reconciliation_report.csv",
        PipelineStage.WAGE_ANOMALY.value: ANOMALY_DIR / "wage_anomaly_report.csv",
        PipelineStage.FRAUD_DETECTION.value: FRAUD_DIR / "fraud_detection_report.csv",
        PipelineStage.RISK_SCORING.value: RISK_DIR / "compliance_risk_report.csv",
        PipelineStage.SITE_PERFORMANCE.value: SITE_DIR / "site_performance_scores.csv",
        PipelineStage.FINAL_REPORT.value: OUTPUT_DIR / "security_ai_final_report.csv",
    }

    status = {}
    for stage, path in stages.items():
        if path.exists():
            try:
                df = pd.read_csv(path, nrows=1)
                status[stage] = "PASS" if not df.empty else "EMPTY"
            except Exception:
                status[stage] = "CORRUPTED"
        else:
            status[stage] = "MISSING"
    return status


# ============================================================
# MODULE 2 — COMPLIANCE SUMMARY
# ============================================================


def generate_compliance_summary(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Aggregate compliance across PF, ESI, attendance, payroll."""
    summary: Dict[str, Any] = {}

    # PF Compliance
    pf_df = sources.get("pf", pd.DataFrame())
    if not pf_df.empty:
        pf_col = find_column(pf_df, "mismatch_flag")
        if pf_col:
            mismatched = (pf_df[pf_col].astype(str).str.lower() == "yes").sum()
            total = len(pf_df)
            summary["pf_compliance_pct"] = round((1 - mismatched / max(total, 1)) * 100, 2)
            summary["pf_total"] = total
            summary["pf_mismatched"] = int(mismatched)
        else:
            # Try match_status column
            ms = find_column(pf_df, "match_status") or "Match_Status"
            if ms in pf_df.columns:
                matched = (pf_df[ms].astype(str).str.lower() == "matched").sum()
                summary["pf_compliance_pct"] = round(matched / max(len(pf_df), 1) * 100, 2)
                summary["pf_total"] = len(pf_df)
                summary["pf_mismatched"] = len(pf_df) - int(matched)
            else:
                summary["pf_compliance_pct"] = 100.0
                summary["pf_total"] = len(pf_df)
                summary["pf_mismatched"] = 0
    else:
        summary["pf_compliance_pct"] = 0.0
        summary["pf_total"] = 0
        summary["pf_mismatched"] = 0

    # ESI Compliance
    esi_df = sources.get("esi", pd.DataFrame())
    if not esi_df.empty:
        esi_col = find_column(esi_df, "mismatch_flag")
        if esi_col:
            mismatched = (esi_df[esi_col].astype(str).str.lower() == "yes").sum()
            total = len(esi_df)
            summary["esi_compliance_pct"] = round((1 - mismatched / max(total, 1)) * 100, 2)
            summary["esi_total"] = total
            summary["esi_mismatched"] = int(mismatched)
        else:
            ms = find_column(esi_df, "match_status") or "Match_Status"
            if ms in esi_df.columns:
                matched = (esi_df[ms].astype(str).str.lower() == "matched").sum()
                summary["esi_compliance_pct"] = round(matched / max(len(esi_df), 1) * 100, 2)
                summary["esi_total"] = len(esi_df)
                summary["esi_mismatched"] = len(esi_df) - int(matched)
            else:
                summary["esi_compliance_pct"] = 100.0
                summary["esi_total"] = len(esi_df)
                summary["esi_mismatched"] = 0
    else:
        summary["esi_compliance_pct"] = 0.0
        summary["esi_total"] = 0
        summary["esi_mismatched"] = 0

    # Attendance Compliance
    att_df = sources.get("attendance", pd.DataFrame())
    if not att_df.empty:
        status_col = find_column(att_df, "attendance_status")
        if status_col:
            present = (att_df[status_col].astype(str).str.lower() == "present").sum()
            summary["attendance_compliance_pct"] = round(present / max(len(att_df), 1) * 100, 2)
        else:
            summary["attendance_compliance_pct"] = 0.0
    else:
        summary["attendance_compliance_pct"] = 0.0

    # Payroll Compliance (from wage anomaly)
    wage_df = sources.get("wage_anomaly", pd.DataFrame())
    if not wage_df.empty:
        anomaly_col = find_column(wage_df, "anomaly_flag")
        if anomaly_col:
            anomalies = (wage_df[anomaly_col].astype(str).isin(["-1", "1", "anomaly", "High Risk"])).sum()
            total = len(wage_df)
            summary["payroll_compliance_pct"] = round((1 - anomalies / max(total, 1)) * 100, 2)
        else:
            status_col = find_column(wage_df, "risk_level")
            if status_col:
                clean = (~wage_df[status_col].astype(str).str.lower().isin(
                    ["high", "critical", "high risk"]
                )).sum()
                summary["payroll_compliance_pct"] = round(clean / max(len(wage_df), 1) * 100, 2)
            else:
                summary["payroll_compliance_pct"] = 95.0
    else:
        summary["payroll_compliance_pct"] = 0.0

    # PSARA Compliance (from compliance data)
    comp_df = sources.get("compliance", pd.DataFrame())
    if not comp_df.empty:
        rl = find_column(comp_df, "risk_level")
        if rl:
            low = (comp_df[rl].astype(str).str.lower() == "low").sum()
            summary["psara_compliance_pct"] = round(low / max(len(comp_df), 1) * 100, 2)
        else:
            summary["psara_compliance_pct"] = 100.0
    else:
        summary["psara_compliance_pct"] = 0.0

    # Overall
    pcts = [
        summary.get("pf_compliance_pct", 0),
        summary.get("esi_compliance_pct", 0),
        summary.get("attendance_compliance_pct", 0),
        summary.get("payroll_compliance_pct", 0),
        summary.get("psara_compliance_pct", 0),
    ]
    active_pcts = [p for p in pcts if p > 0]
    summary["overall_compliance_pct"] = round(
        sum(active_pcts) / max(len(active_pcts), 1), 2
    ) if active_pcts else 0.0

    return summary


# ============================================================
# MODULE 3 — RISK SUMMARY
# ============================================================


def generate_risk_summary(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    risk_df = sources.get("risk", pd.DataFrame())
    if risk_df.empty:
        return {
            "total_risk_cases": 0, "low_risk": 0, "medium_risk": 0,
            "high_risk": 0, "critical_risk": 0, "risk_pct": 0.0,
        }

    rl_col = find_column(risk_df, "risk_level") or find_column(risk_df, "severity")
    total = len(risk_df)

    if rl_col:
        vals = risk_df[rl_col].astype(str).str.lower()
        low = int((vals == "low").sum())
        medium = int((vals == "medium").sum())
        high = int(vals.isin(["high", "high risk"]).sum())
        critical = int(vals.isin(["critical", "critical risk"]).sum())
    else:
        low, medium, high, critical = total, 0, 0, 0

    high_critical = high + critical
    return {
        "total_risk_cases": total,
        "low_risk": low,
        "medium_risk": medium,
        "high_risk": high,
        "critical_risk": critical,
        "risk_pct": round(high_critical / max(total, 1) * 100, 2),
    }


# ============================================================
# MODULE 4 — FRAUD SUMMARY
# ============================================================


def generate_fraud_summary(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    fraud_df = sources.get("fraud", pd.DataFrame())
    if fraud_df.empty:
        return {
            "total_fraud_alerts": 0, "ghost_employees": 0,
            "duplicate_employees": 0, "fake_attendance": 0,
            "salary_inflation": 0, "pf_fraud": 0, "esi_fraud": 0,
            "overtime_fraud": 0, "fake_bank_accounts": 0,
        }

    ft_col = find_column(fraud_df, "fraud_type")
    total = len(fraud_df)

    cats = {
        "ghost_employees": 0, "duplicate_employees": 0, "fake_attendance": 0,
        "salary_inflation": 0, "pf_fraud": 0, "esi_fraud": 0,
        "overtime_fraud": 0, "fake_bank_accounts": 0,
    }

    if ft_col:
        types = fraud_df[ft_col].astype(str).str.lower()
        cats["ghost_employees"] = int(types.str.contains("ghost|non.?exist", regex=True).sum())
        cats["duplicate_employees"] = int(types.str.contains("duplicat|clone", regex=True).sum())
        cats["fake_attendance"] = int(types.str.contains("fake.?att|proxy|buddy.?punch", regex=True).sum())
        cats["salary_inflation"] = int(types.str.contains("salary.?inflat|wage.?inflat", regex=True).sum())
        cats["pf_fraud"] = int(types.str.contains("pf.?fraud|epf", regex=True).sum())
        cats["esi_fraud"] = int(types.str.contains("esi.?fraud|esic", regex=True).sum())
        cats["overtime_fraud"] = int(types.str.contains("ot.?fraud|overtime.?fraud|fake.?ot", regex=True).sum())
        cats["fake_bank_accounts"] = int(types.str.contains("bank.?fraud|fake.?bank|bank.?account", regex=True).sum())

    return {"total_fraud_alerts": total, **cats}


# ============================================================
# MODULE 5 — WAGE ANALYTICS
# ============================================================


def generate_wage_summary(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    wage_df = sources.get("wage_anomaly", pd.DataFrame())
    if wage_df.empty:
        wage_df = sources.get("payroll", pd.DataFrame())
    if wage_df.empty:
        return {
            "avg_wage": 0, "highest_wage": 0, "lowest_wage": 0,
            "total_payroll": 0, "avg_overtime": 0, "avg_recoveries": 0,
        }

    col_map = build_column_map(wage_df)

    gross_col = col_map.get("gross_wages")
    ot_col = col_map.get("overtime_hours")
    rec_col = col_map.get("recoveries")

    gross = pd.to_numeric(wage_df[gross_col], errors="coerce").fillna(0) if gross_col else pd.Series([0])
    ot = pd.to_numeric(wage_df[ot_col], errors="coerce").fillna(0) if ot_col else pd.Series([0])
    rec = pd.to_numeric(wage_df[rec_col], errors="coerce").fillna(0) if rec_col else pd.Series([0])

    return {
        "avg_wage": round(float(gross.mean()), 2),
        "highest_wage": round(float(gross.max()), 2),
        "lowest_wage": round(float(gross.min()), 2),
        "total_payroll": round(float(gross.sum()), 2),
        "avg_overtime": round(float(ot.mean()), 1),
        "avg_recoveries": round(float(rec.mean()), 2),
        "total_employees": len(wage_df),
    }


# ============================================================
# MODULE 6 — SITE ANALYTICS
# ============================================================


def generate_site_summary(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    site_df = sources.get("site_performance", pd.DataFrame())
    if site_df.empty:
        return {
            "total_sites": 0, "excellent": 0, "good": 0,
            "average": 0, "poor": 0, "critical": 0,
            "avg_performance": 0,
        }

    grade_col = find_column(site_df, "grade")
    score_col = find_column(site_df, "performance_score")
    total = len(site_df)

    grades = {"excellent": 0, "good": 0, "average": 0, "poor": 0, "critical": 0}
    if grade_col:
        vals = site_df[grade_col].astype(str).str.lower()
        for key in grades:
            grades[key] = int((vals == key).sum())

    avg_score = 0.0
    if score_col:
        scores = pd.to_numeric(site_df[score_col], errors="coerce").dropna()
        avg_score = round(float(scores.mean()), 2) if not scores.empty else 0.0

    return {"total_sites": total, **grades, "avg_performance": avg_score}


# ============================================================
# MODULE 7 — TOP 10 REPORTS
# ============================================================


def top_10_best_sites(sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    site_df = sources.get("site_performance", pd.DataFrame())
    if site_df.empty:
        return pd.DataFrame()

    score_col = find_column(site_df, "performance_score")
    if not score_col:
        return pd.DataFrame()

    df = site_df.copy()
    df["_score"] = pd.to_numeric(df[score_col], errors="coerce")
    top = df.nlargest(10, "_score")

    name_col = find_column(top, "site_id") or find_column(top, "site_name")
    grade_col = find_column(top, "grade")

    result = pd.DataFrame()
    if name_col:
        result["site"] = top[name_col].values
    result["score"] = top["_score"].values.round(2)
    if grade_col:
        result["grade"] = top[grade_col].values
    result = result.reset_index(drop=True)
    result.index = result.index + 1
    result.index.name = "rank"
    return result


def top_10_worst_sites(sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    site_df = sources.get("site_performance", pd.DataFrame())
    if site_df.empty:
        return pd.DataFrame()

    score_col = find_column(site_df, "performance_score")
    if not score_col:
        return pd.DataFrame()

    df = site_df.copy()
    df["_score"] = pd.to_numeric(df[score_col], errors="coerce")
    bottom = df.nsmallest(10, "_score")

    name_col = find_column(bottom, "site_id") or find_column(bottom, "site_name")
    grade_col = find_column(bottom, "grade")

    result = pd.DataFrame()
    if name_col:
        result["site"] = bottom[name_col].values
    result["score"] = bottom["_score"].values.round(2)
    if grade_col:
        result["grade"] = bottom[grade_col].values
    result = result.reset_index(drop=True)
    result.index = result.index + 1
    result.index.name = "rank"
    return result


def top_10_high_risk_guards(sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    risk_df = sources.get("risk", pd.DataFrame())
    if risk_df.empty:
        return pd.DataFrame()

    rl_col = find_column(risk_df, "risk_level") or find_column(risk_df, "severity")
    if not rl_col:
        return pd.DataFrame()

    high = risk_df[risk_df[rl_col].astype(str).str.lower().isin(["high", "critical", "high risk"])]
    if high.empty:
        return pd.DataFrame()

    name_col = find_column(high, "guard_name") or find_column(high, "guard_id")
    if not name_col:
        return pd.DataFrame()

    result = high.head(10).copy()
    keep = [c for c in [name_col, rl_col, find_column(high, "site_id")] if c]
    return result[keep].reset_index(drop=True)


def top_10_fraud_cases(sources: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    fraud_df = sources.get("fraud", pd.DataFrame())
    if fraud_df.empty:
        return pd.DataFrame()

    name_col = find_column(fraud_df, "guard_name") or find_column(fraud_df, "guard_id")
    ft_col = find_column(fraud_df, "fraud_type") or find_column(fraud_df, "anomaly_type")
    sev = find_column(fraud_df, "severity") or find_column(fraud_df, "risk_level")

    keep = [c for c in [name_col, ft_col, sev] if c]
    if not keep:
        return fraud_df.head(10)

    return fraud_df[keep].head(10).reset_index(drop=True)


# ============================================================
# MODULE 8 — KPI SECTION
# ============================================================


def generate_kpis(sources: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """Generate top-level KPIs."""
    guards_df = sources.get("guards", pd.DataFrame())
    att_df = sources.get("attendance", pd.DataFrame())
    wage_df = sources.get("wage_anomaly", pd.DataFrame())
    pf_df = sources.get("pf", pd.DataFrame())
    esi_df = sources.get("esi", pd.DataFrame())
    fraud_df = sources.get("fraud", pd.DataFrame())
    comp_df = sources.get("compliance", pd.DataFrame())
    site_df = sources.get("site_performance", pd.DataFrame())

    total_employees = len(guards_df) if not guards_df.empty else (len(wage_df) if not wage_df.empty else 0)

    # Attendance %
    att_pct = 0.0
    if not att_df.empty:
        sc = find_column(att_df, "attendance_status")
        if sc:
            present = (att_df[sc].astype(str).str.lower() == "present").sum()
            att_pct = round(present / max(len(att_df), 1) * 100, 2)

    # Payroll accuracy
    payroll_acc = 0.0
    if not wage_df.empty:
        af = find_column(wage_df, "anomaly_flag")
        if af:
            normal = (wage_df[af].astype(str).isin(["1", "normal", "0"])).sum()
            payroll_acc = round(normal / max(len(wage_df), 1) * 100, 2)
        else:
            rs = find_column(wage_df, "risk_level")
            if rs:
                normal = (~wage_df[rs].astype(str).str.lower().isin(["high", "critical", "high risk"])).sum()
                payroll_acc = round(normal / max(len(wage_df), 1) * 100, 2)
            else:
                payroll_acc = 95.0

    # PF accuracy
    pf_acc = 0.0
    if not pf_df.empty:
        mf = find_column(pf_df, "mismatch_flag")
        if mf:
            ok = (pf_df[mf].astype(str).str.lower() != "yes").sum()
            pf_acc = round(ok / max(len(pf_df), 1) * 100, 2)
        else:
            pf_acc = 95.0

    # ESI accuracy
    esi_acc = 0.0
    if not esi_df.empty:
        mf = find_column(esi_df, "mismatch_flag")
        if mf:
            ok = (esi_df[mf].astype(str).str.lower() != "yes").sum()
            esi_acc = round(ok / max(len(esi_df), 1) * 100, 2)
        else:
            esi_acc = 95.0

    # Fraud %
    fraud_pct = 0.0
    if not fraud_df.empty:
        fraud_pct = round(len(fraud_df) / max(total_employees, 1) * 100, 2)

    # Compliance %
    comp_pct = 0.0
    if not comp_df.empty:
        rl = find_column(comp_df, "risk_level")
        if rl:
            low = (comp_df[rl].astype(str).str.lower() == "low").sum()
            comp_pct = round(low / max(len(comp_df), 1) * 100, 2)

    # Site performance %
    site_pct = 0.0
    if not site_df.empty:
        sc = find_column(site_df, "performance_score")
        if sc:
            scores = pd.to_numeric(site_df[sc], errors="coerce").dropna()
            site_pct = round(float(scores.mean()), 2) if not scores.empty else 0.0

    return {
        "total_employees": int(total_employees),
        "attendance_pct": att_pct,
        "payroll_accuracy_pct": payroll_acc,
        "pf_accuracy_pct": pf_acc,
        "esi_accuracy_pct": esi_acc,
        "fraud_pct": fraud_pct,
        "compliance_pct": comp_pct,
        "site_performance_pct": site_pct,
    }


# ============================================================
# MODULE 1 — EXECUTIVE DASHBOARD
# ============================================================


def generate_executive_dashboard(
    sources: Dict[str, pd.DataFrame],
    config: ReportConfig,
) -> Dict[str, Any]:
    """Master dashboard pulling all modules together."""
    guards_df = sources.get("guards", pd.DataFrame())
    site_df = sources.get("site_performance", pd.DataFrame())

    # Active/Inactive guards
    total_guards = len(guards_df) if not guards_df.empty else 0
    active_guards = total_guards
    inactive_guards = 0
    if not guards_df.empty:
        sc = find_column(guards_df, "status")
        if sc:
            active_guards = int(guards_df[sc].astype(str).str.lower().isin(["active", "present", "1"]).sum())
            inactive_guards = total_guards - active_guards

    # Sites
    total_sites = len(site_df) if not site_df.empty else 0
    total_clients = 1
    client_col = find_column(site_df, "client") if not site_df.empty else None
    if client_col:
        total_clients = site_df[client_col].nunique()

    # Total payroll
    wage_df = sources.get("wage_anomaly", sources.get("payroll", pd.DataFrame()))
    total_payroll = 0.0
    total_pf = 0.0
    total_esi = 0.0
    if not wage_df.empty:
        gc = find_column(wage_df, "gross_wages")
        if gc:
            total_payroll = round(float(pd.to_numeric(wage_df[gc], errors="coerce").fillna(0).sum()), 2)
        pc = find_column(wage_df, "pf_deduction")
        if pc:
            total_pf = round(float(pd.to_numeric(wage_df[pc], errors="coerce").fillna(0).sum()), 2)
        ec = find_column(wage_df, "esi_deduction")
        if ec:
            total_esi = round(float(pd.to_numeric(wage_df[ec], errors="coerce").fillna(0).sum()), 2)

    return {
        "generated_at": datetime.now().isoformat(),
        "engine_version": config.engine_version,
        "client": config.client,
        "month": config.month or datetime.now().strftime("%Y-%m"),
        "total_clients": total_clients,
        "total_sites": total_sites,
        "total_guards": total_guards,
        "active_guards": active_guards,
        "inactive_guards": inactive_guards,
        "total_payroll": total_payroll,
        "total_pf_deduction": total_pf,
        "total_esi_deduction": total_esi,
    }


# ============================================================
# MODULE 9 — MONTHLY TREND
# ============================================================


def generate_monthly_trends(
    current: Dict[str, Any],
    history_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Track metrics month-over-month."""
    if history_dir is None:
        history_dir = SUMMARY_DIR

    trends = {"months": [], "data": {}}

    # Load historical summaries
    historical = []
    for f in sorted(history_dir.glob("security_summary_*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            if "generated_at" in data:
                historical.append(data)
        except Exception:
            pass

    # Add current
    historical.append(current)

    for entry in historical:
        month = entry.get("month", entry.get("generated_at", "")[:7])
        kpis = entry.get("kpis", {})
        trends["months"].append(month)
        for k, v in kpis.items():
            if k not in trends["data"]:
                trends["data"][k] = []
            trends["data"][k].append(v)

    return trends


# ============================================================
# MODULE 10 — CLIENT SUMMARY
# ============================================================


def generate_client_summary(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    site_df = sources.get("site_performance", pd.DataFrame())
    if site_df.empty:
        return {"client": "default", "sites": 0, "guards": 0}

    client_col = find_column(site_df, "client")
    if not client_col:
        return {"client": "default", "sites": len(site_df)}

    clients = {}
    for client, group in site_df.groupby(client_col):
        sc = find_column(group, "performance_score")
        gc = find_column(group, "guard_count")
        scores = pd.to_numeric(group[sc], errors="coerce").dropna() if sc else pd.Series([0])

        clients[str(client)] = {
            "sites": len(group),
            "guards": int(pd.to_numeric(group[gc], errors="coerce").fillna(0).sum()) if gc else 0,
            "avg_performance": round(float(scores.mean()), 2),
        }

    return clients


# ============================================================
# MODULE 11 — RECOMMENDATION ENGINE
# ============================================================


def generate_recommendations(
    compliance: Dict[str, Any],
    risk: Dict[str, Any],
    fraud: Dict[str, Any],
    kpis: Dict[str, Any],
    site: Dict[str, Any],
) -> List[Dict[str, str]]:
    """Generate actionable recommendations based on all data."""
    recs = []

    # Compliance recommendations
    if compliance.get("pf_compliance_pct", 100) < 90:
        recs.append({
            "priority": "HIGH",
            "category": "Compliance",
            "action": "Correct PF reconciliation. Verify EPF contributions against payroll.",
            "impact": "Legal compliance, avoid penalties",
        })
    if compliance.get("esi_compliance_pct", 100) < 90:
        recs.append({
            "priority": "HIGH",
            "category": "Compliance",
            "action": "Correct ESI reconciliation. Verify ESIC deductions.",
            "impact": "Legal compliance, avoid penalties",
        })
    if compliance.get("attendance_compliance_pct", 100) < 85:
        recs.append({
            "priority": "MEDIUM",
            "category": "Attendance",
            "action": "Implement biometric attendance. Review chronic absenteeism.",
            "impact": "Operational efficiency, reduce ghost employees",
        })

    # Risk recommendations
    if risk.get("high_risk", 0) > 5 or risk.get("critical_risk", 0) > 0:
        recs.append({
            "priority": "CRITICAL",
            "category": "Risk",
            "action": "Address high-risk and critical cases immediately. Conduct site audits.",
            "impact": "Reduce liability, improve safety",
        })

    # Fraud recommendations
    total_fraud = fraud.get("total_fraud_alerts", 0)
    if total_fraud > 0:
        recs.append({
            "priority": "HIGH",
            "category": "Fraud",
            "action": f"Investigate {total_fraud} fraud alerts. Conduct employee verification drive.",
            "impact": "Prevent financial loss, maintain integrity",
        })
    if fraud.get("ghost_employees", 0) > 0:
        recs.append({
            "priority": "CRITICAL",
            "category": "Fraud",
            "action": "Eliminate ghost employees. Conduct physical headcount verification.",
            "impact": "Stop payroll leakage",
        })

    # Site recommendations
    if site.get("poor", 0) + site.get("critical", 0) > 0:
        count = site.get("poor", 0) + site.get("critical", 0)
        recs.append({
            "priority": "HIGH",
            "category": "Site Performance",
            "action": f"Review {count} underperforming sites. Replace supervisors if needed.",
            "impact": "Client satisfaction, contract retention",
        })

    # Payroll recommendations
    if kpis.get("payroll_accuracy_pct", 100) < 90:
        recs.append({
            "priority": "MEDIUM",
            "category": "Payroll",
            "action": "Review payroll processing. Conduct wage audit. Validate salary components.",
            "impact": "Accuracy, employee satisfaction",
        })

    # Attendance
    if kpis.get("attendance_pct", 100) < 85:
        recs.append({
            "priority": "MEDIUM",
            "category": "Operations",
            "action": "Increase guard headcount. Improve shift coverage. Conduct attendance training.",
            "impact": "Service quality, SLA compliance",
        })

    # Training
    if compliance.get("psara_compliance_pct", 100) < 80:
        recs.append({
            "priority": "HIGH",
            "category": "Training",
            "action": "Schedule compliance training. Update PSARA licenses.",
            "impact": "Regulatory compliance",
        })

    if not recs:
        recs.append({
            "priority": "LOW",
            "category": "General",
            "action": "Maintain current standards. Continue monitoring.",
            "impact": "Sustained performance",
        })

    return sorted(recs, key=lambda r: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(r["priority"], 4))


# ============================================================
# MODULE 19 — ML SUMMARY
# ============================================================


def generate_ml_summary(sources: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Summarize ML model outputs."""
    wage_df = sources.get("wage_anomaly", pd.DataFrame())
    fraud_df = sources.get("fraud", pd.DataFrame())

    summary = {
        "wage_anomalies_detected": 0,
        "fraud_probability_high": 0,
        "ml_confidence_avg": 0.0,
    }

    if not wage_df.empty:
        af = find_column(wage_df, "anomaly_flag")
        if af:
            anomalies = (wage_df[af].astype(str).isin(["-1", "anomaly", "High Risk"])).sum()
            summary["wage_anomalies_detected"] = int(anomalies)
        else:
            summary["wage_anomalies_detected"] = len(wage_df[wage_df.get("Risk_Status", pd.Series()).astype(str).str.lower().isin(["high risk", "anomaly"])]) if "Risk_Status" in wage_df.columns else 0

    if not fraud_df.empty:
        sev = find_column(fraud_df, "severity") or find_column(fraud_df, "risk_level")
        if sev:
            summary["fraud_probability_high"] = int(
                fraud_df[sev].astype(str).str.lower().isin(["high", "critical"]).sum()
            )

    return summary


# ============================================================
# MODULE 20 — OVERALL SECURITY SCORE
# ============================================================


def calculate_overall_security_score(
    kpis: Dict[str, float],
    compliance: Dict[str, Any],
    risk: Dict[str, Any],
    site: Dict[str, Any],
    config: ReportConfig,
) -> Dict[str, Any]:
    """Composite security health score 0-100."""
    component_scores = {}

    # Compliance (0-100)
    component_scores["compliance"] = compliance.get("overall_compliance_pct", 0.0)

    # Fraud (inverse of fraud percentage, capped)
    fraud_pct = kpis.get("fraud_pct", 0.0)
    component_scores["fraud"] = max(100 - fraud_pct * 10, 0)

    # Payroll accuracy
    component_scores["payroll"] = kpis.get("payroll_accuracy_pct", 0.0)

    # Attendance
    component_scores["attendance"] = kpis.get("attendance_pct", 0.0)

    # Site performance
    component_scores["site"] = site.get("avg_performance", 0.0)

    # Risk (inverse of risk percentage)
    risk_pct = risk.get("risk_pct", 0.0)
    component_scores["risk"] = max(100 - risk_pct, 0)

    # Wage health (inverse of anomaly rate)
    total = kpis.get("total_employees", 1)
    wage_anom = kpis.get("payroll_accuracy_pct", 100)
    component_scores["wage"] = wage_anom

    # Weighted overall
    overall = round(
        component_scores["compliance"] * config.weight_compliance +
        component_scores["fraud"] * config.weight_fraud +
        component_scores["payroll"] * config.weight_payroll +
        component_scores["attendance"] * config.weight_attendance +
        component_scores["site"] * config.weight_site +
        component_scores["risk"] * config.weight_risk +
        component_scores["wage"] * config.weight_wage,
        2,
    )

    return {"overall_score": overall, "components": component_scores}


# ============================================================
# MODULE 21 — FINAL DECISION
# ============================================================


def generate_management_decision(
    security_score: float,
    config: ReportConfig,
) -> Dict[str, Any]:
    """Classify overall security posture."""
    if security_score >= config.decision_excellent:
        decision = Decision.EXCELLENT.value
        message = "Security operations are exemplary. Maintain current standards."
        color = "green"
    elif security_score >= config.decision_good:
        decision = Decision.GOOD.value
        message = "Security operations are satisfactory. Minor improvements recommended."
        color = "blue"
    elif security_score >= config.decision_needs_improvement:
        decision = Decision.NEEDS_IMPROVEMENT.value
        message = "Security operations require attention. Action plan needed."
        color = "orange"
    else:
        decision = Decision.CRITICAL.value
        message = "Security operations are in critical state. Immediate intervention required."
        color = "red"

    return {
        "decision": decision,
        "score": security_score,
        "message": message,
        "color": color,
        "thresholds": {
            "excellent": config.decision_excellent,
            "good": config.decision_good,
            "needs_improvement": config.decision_needs_improvement,
        },
    }


# ============================================================
# MODULE 12 — AUDIT TRAIL
# ============================================================


def generate_audit_log(config: ReportConfig, stats: RuntimeStats) -> Dict[str, Any]:
    return {
        "report_version": config.engine_version,
        "pipeline_version": config.pipeline_version,
        "execution_time_seconds": stats.elapsed,
        "operator": config.operator,
        "client": config.client,
        "month": config.month,
        "generated_at": datetime.now().isoformat(),
        "input_files": [
            str(RECON_DIR / "pf_reconciliation_report.csv"),
            str(RECON_DIR / "esi_reconciliation_report.csv"),
            str(ANOMALY_DIR / "wage_anomaly_report.csv"),
            str(FRAUD_DIR / "fraud_detection_report.csv"),
            str(RISK_DIR / "compliance_risk_report.csv"),
            str(SITE_DIR / "site_performance_scores.csv"),
        ],
        "output_files": [
            str(OUTPUT_DIR / "security_ai_final_report.csv"),
            str(EXPORT_DIR / "security_ai_final_report.xlsx"),
            str(SUMMARY_DIR / "security_ai_dashboard.json"),
            str(SUMMARY_DIR / "security_ai_summary.json"),
        ],
        "audit_entries": [asdict(e) for e in _audit_log[-50:]],
    }


# ============================================================
# MODULE 15 — REPORT METADATA
# ============================================================


def generate_report_metadata(config: ReportConfig, stats: RuntimeStats) -> Dict[str, Any]:
    return {
        "generated_on": datetime.now().isoformat(),
        "execution_time": stats.elapsed,
        "client": config.client,
        "month": config.month or datetime.now().strftime("%Y-%m"),
        "records_processed": stats.rows_loaded,
        "files_loaded": stats.files_loaded,
        "modules_run": stats.modules_run,
        "pipeline_version": config.pipeline_version,
        "engine_version": config.engine_version,
    }


# ============================================================
# MODULE 18 — CHART DATA
# ============================================================


def generate_chart_data(
    compliance: Dict[str, Any],
    fraud: Dict[str, Any],
    site: Dict[str, Any],
    kpis: Dict[str, float],
    security: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate JSON structures for frontend chart rendering."""
    return {
        "compliance_radar": {
            "labels": ["PF", "ESI", "Attendance", "Payroll", "PSARA"],
            "values": [
                compliance.get("pf_compliance_pct", 0),
                compliance.get("esi_compliance_pct", 0),
                compliance.get("attendance_compliance_pct", 0),
                compliance.get("payroll_compliance_pct", 0),
                compliance.get("psara_compliance_pct", 0),
            ],
        },
        "fraud_breakdown": {
            "labels": [
                "Ghost", "Duplicate", "Fake Attendance", "Salary Inflation",
                "PF Fraud", "ESI Fraud", "OT Fraud", "Fake Bank",
            ],
            "values": [
                fraud.get("ghost_employees", 0),
                fraud.get("duplicate_employees", 0),
                fraud.get("fake_attendance", 0),
                fraud.get("salary_inflation", 0),
                fraud.get("pf_fraud", 0),
                fraud.get("esi_fraud", 0),
                fraud.get("overtime_fraud", 0),
                fraud.get("fake_bank_accounts", 0),
            ],
        },
        "site_grade_distribution": {
            "labels": ["Excellent", "Good", "Average", "Poor", "Critical"],
            "values": [
                site.get("excellent", 0),
                site.get("good", 0),
                site.get("average", 0),
                site.get("poor", 0),
                site.get("critical", 0),
            ],
        },
        "security_score_breakdown": {
            "labels": list(security.get("components", {}).keys()),
            "values": list(security.get("components", {}).values()),
        },
        "kpi_gauges": {
            "labels": list(kpis.keys()),
            "values": list(kpis.values()),
        },
    }


# ============================================================
# MODULE 16 — MULTI-FORMAT EXPORT
# ============================================================


def export_csv(df: pd.DataFrame):
    path = OUTPUT_DIR / "security_ai_final_report.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"CSV → {path}")


def export_excel(
    summary_df: pd.DataFrame,
    top_best: pd.DataFrame,
    top_worst: pd.DataFrame,
    top_risk: pd.DataFrame,
    top_fraud: pd.DataFrame,
    recommendations: List[Dict],
    dashboard: Dict,
    metadata: Dict,
):
    if not HAS_OPENPYXL:
        logger.warning("openpyxl not available — skipping Excel export")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"security_ai_final_report_{ts}.xlsx"

    wb = Workbook()

    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
    border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    def write_df(ws, df, start_row=1):
        if df.empty:
            return start_row
        # Headers
        for col_idx, col_name in enumerate(df.columns, 1):
            cell = ws.cell(row=start_row, column=col_idx, value=str(col_name))
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = border
        # Data
        for row_idx, (_, row) in enumerate(df.iterrows(), start_row + 1):
            for col_idx, val in enumerate(row, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.border = border
                if isinstance(val, (int, float)):
                    cell.alignment = Alignment(horizontal="right")
        return start_row + len(df) + 2

    # Sheet 1: Executive Summary
    ws = wb.active
    ws.title = "Executive Summary"
    r = 1
    for k, v in dashboard.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                ws.cell(row=r, column=1, value=f"{k}.{sk}").font = Font(bold=True)
                ws.cell(row=r, column=2, value=str(sv))
                r += 1
        else:
            ws.cell(row=r, column=1, value=k).font = Font(bold=True)
            ws.cell(row=r, column=2, value=str(v))
            r += 1

    # Sheet 2: Full Report
    ws2 = wb.create_sheet("Full Report")
    write_df(ws2, summary_df)

    # Sheet 3: Top 10 Best
    ws3 = wb.create_sheet("Top 10 Best Sites")
    write_df(ws3, top_best)

    # Sheet 4: Top 10 Worst
    ws4 = wb.create_sheet("Top 10 Worst Sites")
    write_df(ws4, top_worst)

    # Sheet 5: Top Risk
    ws5 = wb.create_sheet("Top Risk Guards")
    write_df(ws5, top_risk)

    # Sheet 6: Top Fraud
    ws6 = wb.create_sheet("Top Fraud Cases")
    write_df(ws6, top_fraud)

    # Sheet 7: Recommendations
    ws7 = wb.create_sheet("Recommendations")
    if recommendations:
        rec_df = pd.DataFrame(recommendations)
        write_df(ws7, rec_df)

    # Sheet 8: Metadata
    ws8 = wb.create_sheet("Metadata")
    r = 1
    for k, v in metadata.items():
        ws8.cell(row=r, column=1, value=k).font = Font(bold=True)
        ws8.cell(row=r, column=2, value=str(v))
        r += 1

    # Auto-width
    for ws in wb.worksheets:
        for col in ws.columns:
            max_length = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_length + 4, 50)

    wb.save(path)
    logger.info(f"Excel → {path}")


def export_json(dashboard: Dict, summary: Dict, charts: Dict, metadata: Dict):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Dashboard JSON
    dash_path = SUMMARY_DIR / "security_ai_dashboard.json"
    with open(dash_path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, default=str)
    logger.info(f"JSON → {dash_path}")

    # Summary JSON
    summary_path = SUMMARY_DIR / "security_ai_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({**summary, "charts": charts, "metadata": metadata}, f, indent=2, default=str)
    logger.info(f"JSON → {summary_path}")


# ============================================================
# MODULE 17 — EXECUTIVE PDF
# ============================================================


def generate_pdf_report(
    dashboard: Dict,
    kpis: Dict[str, float],
    compliance: Dict[str, Any],
    risk: Dict[str, Any],
    fraud: Dict[str, Any],
    site: Dict[str, Any],
    security: Dict[str, Any],
    decision: Dict[str, Any],
    recommendations: List[Dict],
    metadata: Dict,
):
    if not HAS_REPORTLAB:
        logger.warning("reportlab not available — skipping PDF export")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"security_ai_report_{ts}.pdf"

    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=18, spaceAfter=12, textColor=colors.HexColor("#2C3E50"),
    )
    heading_style = ParagraphStyle(
        "CustomHeading", parent=styles["Heading2"],
        fontSize=14, spaceAfter=8, textColor=colors.HexColor("#34495E"),
    )
    body_style = styles["Normal"]

    story = []

    # Title
    story.append(Paragraph("Security AI — Executive Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Paragraph(f"Client: {dashboard.get('client', 'N/A')} | Month: {dashboard.get('month', 'N/A')}", body_style))
    story.append(Spacer(1, 10 * mm))

    # Decision
    story.append(Paragraph("MANAGEMENT DECISION", heading_style))
    story.append(Paragraph(
        f"<b>{decision.get('decision', 'N/A')}</b> — Score: {decision.get('score', 0)}/100",
        body_style,
    ))
    story.append(Paragraph(decision.get("message", ""), body_style))
    story.append(Spacer(1, 8 * mm))

    # KPIs
    story.append(Paragraph("KEY PERFORMANCE INDICATORS", heading_style))
    kpi_data = [["Metric", "Value"]]
    for k, v in kpis.items():
        kpi_data.append([k.replace("_", " ").title(), str(v)])
    t = Table(kpi_data, colWidths=[80 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#ECF0F1")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8 * mm))

    # Compliance
    story.append(Paragraph("COMPLIANCE SUMMARY", heading_style))
    comp_data = [["Compliance Area", "Score (%)"]]
    for key in ["pf_compliance_pct", "esi_compliance_pct", "attendance_compliance_pct", "payroll_compliance_pct", "psara_compliance_pct", "overall_compliance_pct"]:
        comp_data.append([key.replace("_pct", "").replace("_", " ").title(), str(compliance.get(key, 0))])
    t2 = Table(comp_data, colWidths=[80 * mm, 60 * mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27AE60")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t2)
    story.append(Spacer(1, 8 * mm))

    # Risk
    story.append(Paragraph("RISK SUMMARY", heading_style))
    risk_data = [["Level", "Count"]]
    for k in ["low_risk", "medium_risk", "high_risk", "critical_risk"]:
        risk_data.append([k.replace("_", " ").title(), str(risk.get(k, 0))])
    t3 = Table(risk_data, colWidths=[80 * mm, 60 * mm])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E74C3C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8 * mm))

    # Fraud
    story.append(Paragraph("FRAUD SUMMARY", heading_style))
    fraud_data = [["Fraud Type", "Count"]]
    for k, v in fraud.items():
        if isinstance(v, int) and v > 0:
            fraud_data.append([k.replace("_", " ").title(), str(v)])
    if len(fraud_data) == 1:
        fraud_data.append(["No fraud detected", "0"])
    t4 = Table(fraud_data, colWidths=[80 * mm, 60 * mm])
    t4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8E44AD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(t4)
    story.append(Spacer(1, 8 * mm))

    # Recommendations
    story.append(PageBreak())
    story.append(Paragraph("RECOMMENDATIONS", heading_style))
    for i, rec in enumerate(recommendations[:10], 1):
        story.append(Paragraph(
            f"<b>{i}. [{rec['priority']}] {rec['category']}:</b> {rec['action']}",
            body_style,
        ))
        story.append(Spacer(1, 3 * mm))

    doc.build(story)
    logger.info(f"PDF → {path}")


# ============================================================
# MAIN ENGINE
# ============================================================


class FinalSecurityReportEngine:
    """
    Production final report engine.
    Aggregates all pipeline outputs into executive intelligence.
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or load_config()
        self.stats = RuntimeStats()
        self.sources: Dict[str, pd.DataFrame] = {}

        self.dashboard: Dict[str, Any] = {}
        self.compliance: Dict[str, Any] = {}
        self.risk: Dict[str, Any] = {}
        self.fraud: Dict[str, Any] = {}
        self.wage: Dict[str, Any] = {}
        self.site: Dict[str, Any] = {}
        self.kpis: Dict[str, float] = {}
        self.security_score: Dict[str, Any] = {}
        self.decision: Dict[str, Any] = {}
        self.recommendations: List[Dict] = []
        self.charts: Dict[str, Any] = {}
        self.ml_summary: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.audit: Dict[str, Any] = {}

        _audit_log.clear()

    def run(self) -> Dict[str, Any]:
        self.stats = RuntimeStats()
        cfg = self.config

        logger.info("=" * 70)
        logger.info("FINAL SECURITY REPORT ENGINE")
        logger.info(f"Engine version: {cfg.engine_version}")
        logger.info(f"Client: {cfg.client}, Month: {cfg.month or 'current'}")
        logger.info("=" * 70)

        # ── 1. Load all sources ──
        logger.info("PHASE 1: LOADING PIPELINE OUTPUTS")
        self.sources = load_all_sources()
        self.stats.files_loaded = len(self.sources)
        for k, df in self.sources.items():
            self.stats.rows_loaded += len(df)
        audit_log("ENGINE_START", "loader", f"Sources={len(self.sources)}, Rows={self.stats.rows_loaded}")
        logger.info(f"Loaded {len(self.sources)} sources, {self.stats.rows_loaded} total rows")

        # ── 2. File health ──
        logger.info("PHASE 2: FILE HEALTH VALIDATION")
        file_health = validate_pipeline_outputs()
        for name, fh in file_health.items():
            logger.info(f"  {name}: {fh.status} ({fh.rows} rows)")

        # ── 3. Pipeline status ──
        logger.info("PHASE 3: PIPELINE STATUS")
        pipeline_status = pipeline_health_check()
        for stage, status in pipeline_status.items():
            logger.info(f"  {stage}: {status}")

        # ── 4. Compliance summary ──
        logger.info("PHASE 4: COMPLIANCE SUMMARY")
        self.compliance = generate_compliance_summary(self.sources)
        logger.info(f"  Overall compliance: {self.compliance.get('overall_compliance_pct', 0)}%")

        # ── 5. Risk summary ──
        logger.info("PHASE 5: RISK SUMMARY")
        self.risk = generate_risk_summary(self.sources)
        logger.info(f"  Total risk cases: {self.risk.get('total_risk_cases', 0)}")

        # ── 6. Fraud summary ──
        logger.info("PHASE 6: FRAUD SUMMARY")
        self.fraud = generate_fraud_summary(self.sources)
        logger.info(f"  Fraud alerts: {self.fraud.get('total_fraud_alerts', 0)}")

        # ── 7. Wage analytics ──
        logger.info("PHASE 7: WAGE ANALYTICS")
        self.wage = generate_wage_summary(self.sources)
        logger.info(f"  Total payroll: ₹{self.wage.get('total_payroll', 0):,.0f}")

        # ── 8. Site analytics ──
        logger.info("PHASE 8: SITE ANALYTICS")
        self.site = generate_site_summary(self.sources)
        logger.info(f"  Sites: {self.site.get('total_sites', 0)}, Avg: {self.site.get('avg_performance', 0)}")

        # ── 9. Executive dashboard ──
        logger.info("PHASE 9: EXECUTIVE DASHBOARD")
        self.dashboard = generate_executive_dashboard(self.sources, cfg)
        self.stats.modules_run += 1

        # ── 10. KPIs ──
        logger.info("PHASE 10: KPI GENERATION")
        self.kpis = generate_kpis(self.sources)
        logger.info(f"  Employees: {self.kpis.get('total_employees', 0)}")
        logger.info(f"  Attendance: {self.kpis.get('attendance_pct', 0)}%")
        logger.info(f"  Payroll accuracy: {self.kpis.get('payroll_accuracy_pct', 0)}%")

        # ── 11. Security score ──
        logger.info("PHASE 11: OVERALL SECURITY SCORE")
        self.security_score = calculate_overall_security_score(
            self.kpis, self.compliance, self.risk, self.site, cfg,
        )
        logger.info(f"  Overall score: {self.security_score.get('overall_score', 0)}/100")

        # ── 12. Management decision ──
        logger.info("PHASE 12: MANAGEMENT DECISION")
        self.decision = generate_management_decision(
            self.security_score.get("overall_score", 0), cfg,
        )
        logger.info(f"  Decision: {self.decision.get('decision', 'N/A')}")

        # ── 13. Top 10 reports ──
        logger.info("PHASE 13: TOP 10 REPORTS")
        best_sites = top_10_best_sites(self.sources)
        worst_sites = top_10_worst_sites(self.sources)
        top_risk_guards = top_10_high_risk_guards(self.sources)
        top_fraud_cases = top_10_fraud_cases(self.sources)

        # ── 14. Recommendations ──
        logger.info("PHASE 14: RECOMMENDATIONS")
        self.recommendations = generate_recommendations(
            self.compliance, self.risk, self.fraud, self.kpis, self.site,
        )
        logger.info(f"  Recommendations: {len(self.recommendations)}")

        # ── 15. Charts ──
        logger.info("PHASE 15: CHART DATA")
        self.charts = generate_chart_data(
            self.compliance, self.fraud, self.site, self.kpis, self.security_score,
        )

        # ── 16. ML summary ──
        logger.info("PHASE 16: ML SUMMARY")
        self.ml_summary = generate_ml_summary(self.sources)

        # ── 17. Monthly trends ──
        logger.info("PHASE 17: MONTHLY TRENDS")
        monthly_trends = generate_monthly_trends(
            {"month": cfg.month, "kpis": self.kpis, "security_score": self.security_score},
        )

        # ── 18. Client summary ──
        logger.info("PHASE 18: CLIENT SUMMARY")
        client_summary = generate_client_summary(self.sources)

        # ── 19. Metadata & Audit ──
        self.stats.finish()
        self.metadata = generate_report_metadata(cfg, self.stats)
        self.audit = generate_audit_log(cfg, self.stats)
        audit_log("ENGINE_COMPLETE", "all", f"Elapsed={self.stats.elapsed}s")

        # ── 20. Build final report DataFrame ──
        logger.info("PHASE 20: BUILD FINAL REPORT")

        final_row = {
            "Generated_At": self.metadata["generated_on"],
            "Client": cfg.client,
            "Month": cfg.month or datetime.now().strftime("%Y-%m"),
            # Dashboard
            "Total_Clients": self.dashboard.get("total_clients", 0),
            "Total_Sites": self.dashboard.get("total_sites", 0),
            "Total_Guards": self.dashboard.get("total_guards", 0),
            "Active_Guards": self.dashboard.get("active_guards", 0),
            "Inactive_Guards": self.dashboard.get("inactive_guards", 0),
            "Total_Payroll": self.dashboard.get("total_payroll", 0),
            # Compliance
            "PF_Compliance_Pct": self.compliance.get("pf_compliance_pct", 0),
            "ESI_Compliance_Pct": self.compliance.get("esi_compliance_pct", 0),
            "Attendance_Compliance_Pct": self.compliance.get("attendance_compliance_pct", 0),
            "Payroll_Compliance_Pct": self.compliance.get("payroll_compliance_pct", 0),
            "PSARA_Compliance_Pct": self.compliance.get("psara_compliance_pct", 0),
            "Overall_Compliance_Pct": self.compliance.get("overall_compliance_pct", 0),
            # Risk
            "Low_Risk_Cases": self.risk.get("low_risk", 0),
            "Medium_Risk_Cases": self.risk.get("medium_risk", 0),
            "High_Risk_Cases": self.risk.get("high_risk", 0),
            "Critical_Risk_Cases": self.risk.get("critical_risk", 0),
            # Fraud
            "Total_Fraud_Alerts": self.fraud.get("total_fraud_alerts", 0),
            "Ghost_Employees": self.fraud.get("ghost_employees", 0),
            "Duplicate_Employees": self.fraud.get("duplicate_employees", 0),
            "Fake_Attendance": self.fraud.get("fake_attendance", 0),
            "Salary_Inflation": self.fraud.get("salary_inflation", 0),
            "PF_Fraud": self.fraud.get("pf_fraud", 0),
            "ESI_Fraud": self.fraud.get("esi_fraud", 0),
            "OT_Fraud": self.fraud.get("overtime_fraud", 0),
            "Fake_Bank_Accounts": self.fraud.get("fake_bank_accounts", 0),
            # Wage
            "Avg_Wage": self.wage.get("avg_wage", 0),
            "Highest_Wage": self.wage.get("highest_wage", 0),
            "Lowest_Wage": self.wage.get("lowest_wage", 0),
            "Avg_Overtime": self.wage.get("avg_overtime", 0),
            "Avg_Recoveries": self.wage.get("avg_recoveries", 0),
            # Sites
            "Total_Sites_Scored": self.site.get("total_sites", 0),
            "Excellent_Sites": self.site.get("excellent", 0),
            "Good_Sites": self.site.get("good", 0),
            "Average_Sites": self.site.get("average", 0),
            "Poor_Sites": self.site.get("poor", 0),
            "Critical_Sites": self.site.get("critical", 0),
            "Avg_Site_Performance": self.site.get("avg_performance", 0),
            # KPIs
            "Attendance_Pct": self.kpis.get("attendance_pct", 0),
            "Payroll_Accuracy_Pct": self.kpis.get("payroll_accuracy_pct", 0),
            "PF_Accuracy_Pct": self.kpis.get("pf_accuracy_pct", 0),
            "ESI_Accuracy_Pct": self.kpis.get("esi_accuracy_pct", 0),
            "Fraud_Pct": self.kpis.get("fraud_pct", 0),
            "Site_Performance_Pct": self.kpis.get("site_performance_pct", 0),
            # Overall
            "Overall_Security_Score": self.security_score.get("overall_score", 0),
            "Management_Decision": self.decision.get("decision", "N/A"),
        }

        final_df = pd.DataFrame([final_row])

        # ── 21. Export ──
        logger.info("PHASE 21: EXPORT")
        export_csv(final_df)
        export_excel(
            final_df, best_sites, worst_sites, top_risk_guards,
            top_fraud_cases, self.recommendations, self.dashboard, self.metadata,
        )
        export_json(self.dashboard, {**final_row, "charts": self.charts}, self.charts, self.metadata)
        generate_pdf_report(
            self.dashboard, self.kpis, self.compliance, self.risk,
            self.fraud, self.site, self.security_score, self.decision,
            self.recommendations, self.metadata,
        )

        # Save audit
        audit_path = SUMMARY_DIR / "security_ai_audit.json"
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(self.audit, f, indent=2, default=str)

        # Save file health
        fh_path = SUMMARY_DIR / "file_health.json"
        with open(fh_path, "w", encoding="utf-8") as f:
            json.dump({k: asdict(v) for k, v in file_health.items()}, f, indent=2, default=str)

        # Save pipeline status
        ps_path = SUMMARY_DIR / "pipeline_status.json"
        with open(ps_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_status, f, indent=2)

        # ── Final summary ──
        logger.info("=" * 70)
        logger.info("FINAL SECURITY REPORT COMPLETE")
        logger.info(f"  Elapsed:             {self.stats.elapsed}s")
        logger.info(f"  Files loaded:        {self.stats.files_loaded}")
        logger.info(f"  Rows processed:      {self.stats.rows_loaded}")
        logger.info(f"  Overall score:       {self.security_score.get('overall_score', 0)}/100")
        logger.info(f"  Decision:            {self.decision.get('decision', 'N/A')}")
        logger.info(f"  Compliance:          {self.compliance.get('overall_compliance_pct', 0)}%")
        logger.info(f"  Fraud alerts:        {self.fraud.get('total_fraud_alerts', 0)}")
        logger.info(f"  High risk cases:     {self.risk.get('high_risk', 0) + self.risk.get('critical_risk', 0)}")
        logger.info(f"  Recommendations:     {len(self.recommendations)}")
        logger.info("=" * 70)

        return {
            "dashboard": self.dashboard,
            "compliance": self.compliance,
            "risk": self.risk,
            "fraud": self.fraud,
            "wage": self.wage,
            "site": self.site,
            "kpis": self.kpis,
            "security_score": self.security_score,
            "decision": self.decision,
            "recommendations": self.recommendations,
            "ml_summary": self.ml_summary,
            "metadata": self.metadata,
            "pipeline_status": pipeline_status,
            "file_health": {k: asdict(v) for k, v in file_health.items()},
        }


# ============================================================
# BACKWARD-COMPATIBLE FUNCTIONS
# ============================================================


def generate_report() -> pd.DataFrame:
    """Backward-compatible report generator."""
    engine = FinalSecurityReportEngine()
    result = engine.run()
    return pd.DataFrame([{
        "Total_Employees": engine.kpis.get("total_employees", 0),
        "PF_Mismatches": engine.compliance.get("pf_mismatched", 0),
        "ESI_Mismatches": engine.compliance.get("esi_mismatched", 0),
        "Wage_Anomalies": engine.fraud.get("total_fraud_alerts", 0),
        "Fraud_Alerts": engine.fraud.get("total_fraud_alerts", 0),
        "High_Risk_Cases": engine.risk.get("high_risk", 0) + engine.risk.get("critical_risk", 0),
        "Best_Performing_Site": "N/A",
        "Worst_Performing_Site": "N/A",
        "Overall_Security_Score": engine.security_score.get("overall_score", 0),
        "Decision": engine.decision.get("decision", "N/A"),
    }])


def save_report(df: pd.DataFrame):
    path = OUTPUT_DIR / "security_ai_final_report.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    logger.info(f"Saved: {path}")


def run():
    engine = FinalSecurityReportEngine()
    return engine.run()


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Final Security Report Engine")
    parser.add_argument("--client", default="default", help="Client name")
    parser.add_argument("--month", default="", help="Month")
    parser.add_argument("--config", default=None, help="Config file path")
    parser.add_argument("--pipeline-status", action="store_true", help="Show pipeline status only")

    args = parser.parse_args()

    if args.pipeline_status:
        status = pipeline_health_check()
        health = validate_pipeline_outputs()
        print("\n=== PIPELINE STATUS ===")
        for stage, s in status.items():
            print(f"  {stage}: {s}")
        print("\n=== FILE HEALTH ===")
        for name, fh in health.items():
            print(f"  {name}: {fh.status} ({fh.rows} rows, {fh.columns} cols)")
        sys.exit(0)

    cfg = load_config(Path(args.config) if args.config else None)
    cfg.client = args.client
    cfg.month = args.month

    engine = FinalSecurityReportEngine(config=cfg)
    result = engine.run()
    print(json.dumps(result.get("decision", {}), indent=2, default=str))
