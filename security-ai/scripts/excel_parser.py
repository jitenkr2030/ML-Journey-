# security-ai/scripts/excel_parser.py
"""
Production-Grade Excel Parser
Security AI — PF Wages Reconciliation System

Features:
  • Automatic header detection
  • Multi-sheet parsing with intelligent sheet classification
  • Multi-site / multi-location support
  • Employee master extraction
  • Wage extraction
  • Attendance extraction
  • ECR (Electronic Challan cum Return) extraction
  • Site detection from sheet names and cell content
  • Full audit trail with timestamped operations
  • JSON summary output
  • Comprehensive exception handling
  • Runtime statistics
  • Production-grade structured logging
  • Excel and CSV export
  • Data validation and integrity checks
  • Configurable column mapping
  • Deduplication
  • Dry-run mode
"""

import json
import hashlib
import time
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# ============================================================
# LOGGING — Production structured logging
# ============================================================
import logging
import sys

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)
LOG_DATE = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=LOG_DATE,
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("ExcelParser")

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "raw"
OUTPUT_DIR = BASE_DIR / "processed"
EXPORT_DIR = BASE_DIR / "exports"
SUMMARY_DIR = BASE_DIR / "summaries"
LOG_DIR = BASE_DIR / "logs"

for _dir in (RAW_DIR, OUTPUT_DIR, EXPORT_DIR, SUMMARY_DIR, LOG_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# Attach file handler now that log dir exists
_file_handler = logging.FileHandler(LOG_DIR / "parser.log", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
logger.addHandler(_file_handler)

# ============================================================
# CONSTANTS & COLUMN CONFIGURATION
# ============================================================

# Sheet classification keywords (priority order)
SHEET_CLASSIFICATION: Dict[str, List[str]] = {
    "wages":      ["wages", "salary", "salaries", "pay", "remuneration"],
    "matching":   ["matching", "match", "reconciliation", "recon"],
    "admin":      ["admin", "administration", "overhead", "charges"],
    "ecr":        ["ecr", "challan", "return", "pf_return"],
    "difference": ["diff", "difference", "variance", "discrepancy", "mismatch"],
    "attendance": ["attendance", "attend", "present", "days", "duty"],
    "master":     ["master", "employee", "staff", "personnel", "directory"],
}

# Known column name normalisation map
COLUMN_NORMALIZE: Dict[str, str] = {
    "emp name":       "employee_name",
    "employee name":  "employee_name",
    "emp_name":       "employee_name",
    "staff name":     "employee_name",
    "name":           "employee_name",
    "emp id":         "employee_id",
    "employee id":    "employee_id",
    "emp_id":         "employee_id",
    "staff id":       "employee_id",
    "code":           "employee_id",
    "uan":            "uan_number",
    "uan no":         "uan_number",
    "uan number":     "uan_number",
    "uan_no":         "uan_number",
    "pf number":      "pf_number",
    "pf no":          "pf_number",
    "pf_no":          "pf_number",
    "pf a/c no":      "pf_number",
    "gross wages":    "gross_wages",
    "gross":          "gross_wages",
    "basic wages":    "basic_wages",
    "basic":          "basic_wages",
    "basic da":       "basic_wages",
    "basic + da":     "basic_wages",
    "epf wages":      "epf_wages",
    "eps wages":      "eps_wages",
    "edli wages":     "edli_wages",
    "employee epf":   "employee_epf_contribution",
    "employee eps":   "employee_eps_contribution",
    "employer epf":   "employer_epf_contribution",
    "employer eps":   "employer_eps_contribution",
    "employer admin":  "employer_admin_charges",
    "admin charges":   "employer_admin_charges",
    "location":       "site_location",
    "site":           "site_location",
    "site name":      "site_location",
    "branch":         "site_location",
    "unit":           "site_location",
    "month":          "pay_month",
    "year":           "pay_year",
    "days worked":    "days_worked",
    "working days":   "days_worked",
    "days present":   "days_present",
    "ac_01":          "epf_contribution_ac01",
    "ac_02":          "eps_contribution_ac02",
    "ac_10":          "epf_admin_ac10",
    "ac_21":          "edli_ac21",
    "ac_22":          "epf_admin_ac22",
    "ac1":            "epf_contribution_ac01",
    "ac2":            "eps_contribution_ac02",
    "ac10":           "epf_admin_ac10",
    "ac21":           "edli_ac21",
    "ac22":           "epf_admin_ac22",
    "net pay":        "net_pay",
    "total":          "total_deductions",
    "esi":            "esi_contribution",
    "pt":             "professional_tax",
    "tds":            "tds_deduction",
    "ot":             "overtime_hours",
    "overtime":       "overtime_hours",
    "overtime amount": "overtime_amount",
}

# Minimum column match score for fuzzy matching
FUZZY_THRESHOLD = 0.65

# ============================================================
# DATA CLASSES — Runtime stats and audit trail
# ============================================================


@dataclass
class RuntimeStats:
    """Tracks performance and processing metrics."""
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    files_processed: int = 0
    sheets_processed: int = 0
    sheets_skipped: int = 0
    rows_read: int = 0
    rows_cleaned: int = 0
    rows_dropped_empty: int = 0
    rows_dropped_duplicate: int = 0
    employees_found: int = 0
    sites_detected: int = 0
    headers_auto_detected: int = 0
    columns_normalized: int = 0
    errors: int = 0
    warnings: int = 0

    def finish(self):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        end = self.end_time or time.perf_counter()
        return round(end - self.start_time, 3)

    def summary(self) -> Dict[str, Any]:
        d = asdict(self)
        d["elapsed_seconds"] = self.elapsed
        return d


@dataclass
class AuditEntry:
    """Single audit trail entry."""
    timestamp: str
    action: str
    sheet: str
    detail: str
    rows_affected: int = 0
    checksum: str = ""


class AuditTrail:
    """Collects and persists an audit log of all parse operations."""

    def __init__(self):
        self.entries: List[AuditEntry] = []

    def log(
        self,
        action: str,
        sheet: str,
        detail: str,
        rows_affected: int = 0,
        df: Optional[pd.DataFrame] = None,
    ):
        checksum = ""
        if df is not None and not df.empty:
            checksum = hashlib.md5(
                pd.util.hash_pandas_object(df).values.tobytes()
            ).hexdigest()[:12]

        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            sheet=sheet,
            detail=detail,
            rows_affected=rows_affected,
            checksum=checksum,
        )
        self.entries.append(entry)
        logger.debug(f"AUDIT | {action} | {sheet} | {detail}")

    def to_list(self) -> List[Dict]:
        return [asdict(e) for e in self.entries]

    def save(self, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_list(), f, indent=2, default=str)
        logger.info(f"Audit trail saved → {path}")


# ============================================================
# UTILITIES
# ============================================================


def _normalize_header(raw: str) -> str:
    """Convert a raw header string to a normalized key."""
    s = str(raw).strip().lower()
    s = s.replace("\n", " ").replace("\r", " ")
    # collapse whitespace
    s = " ".join(s.split())
    return s


def _fuzzy_ratio(a: str, b: str) -> float:
    """Simple character-set overlap ratio (no external deps)."""
    if not a or not b:
        return 0.0
    set_a, set_b = set(a), set(b)
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def _detect_header_row(df_raw: pd.DataFrame, max_scan: int = 15) -> int:
    """
    Scan the first `max_scan` rows and pick the one with the highest
    'string density' — most likely to be the header row.
    """
    best_row = 0
    best_score = -1

    scan_rows = min(max_scan, len(df_raw))

    for i in range(scan_rows):
        row = df_raw.iloc[i]
        total = len(row)
        if total == 0:
            continue
        str_count = sum(
            1
            for v in row
            if pd.notna(v) and isinstance(v, str) and len(v.strip()) > 0
        )
        score = str_count / total
        # bonus if many unique strings (headers tend to be unique)
        unique_ratio = len(set(str(v) for v in row if pd.notna(v))) / max(total, 1)
        combined = score * 0.6 + unique_ratio * 0.4

        if combined > best_score:
            best_score = combined
            best_row = i

    logger.debug(
        f"Auto-detected header at row {best_row} (score={best_score:.3f})"
    )
    return best_row


def _detect_site_from_df(df: pd.DataFrame) -> List[str]:
    """Try to extract site / location names from the dataframe."""
    sites: set = set()

    # Check column values in any location-like column
    for col in df.columns:
        cl = col.lower()
        if any(k in cl for k in ("location", "site", "branch", "unit", "office")):
            unique_vals = df[col].dropna().astype(str).unique()
            for v in unique_vals:
                v = v.strip()
                if v and len(v) < 80 and v.lower() not in ("nan", "none", "total", ""):
                    sites.add(v.upper())

    return sorted(sites)


def _detect_site_from_sheet_name(sheet_name: str) -> Optional[str]:
    """Extract a site hint from the sheet name itself."""
    parts = sheet_name.replace("_", " ").replace("-", " ").split()
    # Skip generic words
    skip = {
        "wages", "salary", "matching", "admin", "ecr",
        "diff", "difference", "attendance", "master",
        "pf", "recon", "reconciliation", "data", "sheet",
    }
    meaningful = [p for p in parts if p.lower() not in skip and len(p) > 1]
    if meaningful:
        return " ".join(meaningful).upper()
    return None


# ============================================================
# CORE PARSER CLASS
# ============================================================


class ExcelParser:
    """
    Production-grade Excel parser for PF wages reconciliation.

    Handles automatic header detection, multi-sheet parsing,
    site detection, column normalization, deduplication,
    audit trail, and export to CSV/Excel/JSON.
    """

    def __init__(
        self,
        input_path: str,
        output_dir: Optional[Path] = None,
        export_dir: Optional[Path] = None,
        dry_run: bool = False,
        deduplicate: bool = True,
        header_scan_rows: int = 15,
    ):
        self.input_path = Path(input_path)
        self.output_dir = output_dir or OUTPUT_DIR
        self.export_dir = export_dir or EXPORT_DIR
        self.dry_run = dry_run
        self.deduplicate = deduplicate
        self.header_scan_rows = header_scan_rows

        self.stats = RuntimeStats()
        self.audit = AuditTrail()

        # Processed data stores
        self.sheet_data: Dict[str, pd.DataFrame] = {}
        self.employee_master: Optional[pd.DataFrame] = None
        self.site_list: List[str] = []
        self.sheet_classifications: Dict[str, str] = {}  # sheet_name -> category

        # Validation
        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
        if self.input_path.suffix.lower() not in (".xlsx", ".xls", ".xlsm"):
            raise ValueError(f"Unsupported file type: {self.input_path.suffix}")

        for d in (self.output_dir, self.export_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------
    # SHEET CLASSIFICATION
    # ----------------------------------------------------------

    def _classify_sheet(self, sheet_name: str) -> str:
        """Classify a sheet name into a known category."""
        lower = sheet_name.lower().replace("_", " ").replace("-", " ")

        for category, keywords in SHEET_CLASSIFICATION.items():
            for kw in keywords:
                if kw in lower:
                    return category

        return "unknown"

    def _discover_sheets(self, xls: pd.ExcelFile) -> Dict[str, str]:
        """
        Discover and classify all sheets in the workbook.
        Returns {category: actual_sheet_name} mapping.
        """
        mapping: Dict[str, str] = {}
        for sheet_name in xls.sheet_names:
            category = self._classify_sheet(sheet_name)
            self.sheet_classifications[sheet_name] = category
            if category != "unknown":
                mapping[category] = sheet_name
                logger.info(f"Sheet '{sheet_name}' → classified as '{category}'")
            else:
                logger.warning(f"Sheet '{sheet_name}' → unknown classification, will still parse")

        self.stats.sites_detected = len(mapping)
        return mapping

    # ----------------------------------------------------------
    # AUTOMATIC HEADER DETECTION
    # ----------------------------------------------------------

    def _read_with_auto_header(self, xls: pd.ExcelFile, sheet_name: str) -> pd.DataFrame:
        """
        Read a sheet, automatically detecting the header row.
        Returns a clean DataFrame with proper column names.
        """
        # Step 1 — read raw with no header assumption
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)

        if df_raw.empty:
            logger.warning(f"Sheet '{sheet_name}' is empty")
            self.stats.sheets_skipped += 1
            return pd.DataFrame()

        # Step 2 — detect header row
        header_row = _detect_header_row(df_raw, max_scan=self.header_scan_rows)
        self.stats.headers_auto_detected += 1

        # Step 3 — re-read with the detected header
        df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
        logger.info(
            f"Sheet '{sheet_name}': auto-header at row {header_row}, "
            f"shape={df.shape}"
        )

        self.audit.log(
            action="HEADER_DETECTED",
            sheet=sheet_name,
            detail=f"Header at row {header_row}, {len(df.columns)} columns",
            rows_affected=0,
        )

        return df

    # ----------------------------------------------------------
    # COLUMN NORMALIZATION
    # ----------------------------------------------------------

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean column names and map to standardized keys.
        """
        original_cols = list(df.columns)
        new_cols = []
        normalized_count = 0

        for col in original_cols:
            clean = _normalize_header(str(col))

            # Try exact match first
            if clean in COLUMN_NORMALIZE:
                new_cols.append(COLUMN_NORMALIZE[clean])
                normalized_count += 1
                continue

            # Try fuzzy match
            best_match = None
            best_score = 0.0
            for key, mapped in COLUMN_NORMALIZE.items():
                score = _fuzzy_ratio(clean, key)
                if score > best_score:
                    best_score = score
                    best_match = mapped

            if best_score >= FUZZY_THRESHOLD and best_match:
                new_cols.append(best_match)
                normalized_count += 1
            else:
                # Keep original but cleaned
                safe = (
                    clean.replace(" ", "_")
                    .replace(".", "")
                    .replace("/", "_")
                    .replace("(", "")
                    .replace(")", "")
                    .strip("_")
                )
                new_cols.append(safe if safe else f"col_{len(new_cols)}")

        df.columns = new_cols
        self.stats.columns_normalized += normalized_count

        if normalized_count:
            logger.debug(f"Normalized {normalized_count}/{len(new_cols)} columns")

        return df

    # ----------------------------------------------------------
    # DATA CLEANING
    # ----------------------------------------------------------

    def _clean_dataframe(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """
        Full cleaning pipeline:
          1. Remove fully empty rows and columns
          2. Strip whitespace from string cells
          3. Normalize employee names
          4. Deduplicate
          5. Validate data types
        """
        rows_before = len(df)

        # 1. Drop empty
        df = df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        empty_dropped = rows_before - len(df)
        self.stats.rows_dropped_empty += empty_dropped

        # 2. Strip whitespace
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})

        # 3. Employee names → uppercase
        for col in df.columns:
            if "name" in col.lower():
                df[col] = df[col].astype(str).str.upper().str.strip()
                df[col] = df[col].replace({"NAN": np.nan, "NONE": np.nan})

        # 4. Deduplicate
        if self.deduplicate:
            dup_count = df.duplicated().sum()
            if dup_count > 0:
                df = df.drop_duplicates()
                self.stats.rows_dropped_duplicate += int(dup_count)
                logger.info(f"Sheet '{sheet_name}': removed {dup_count} duplicate rows")
                self.audit.log(
                    action="DEDUP",
                    sheet=sheet_name,
                    detail=f"Removed {dup_count} duplicate rows",
                    rows_affected=int(dup_count),
                )

        # 5. Attempt numeric conversion for wage columns
        wage_keywords = (
            "wages", "basic", "gross", "epf", "eps", "edli",
            "contribution", "admin", "pay", "amount", "deduction",
            "total", "esi", "pt", "tds", "overtime",
        )
        for col in df.columns:
            if any(kw in col.lower() for kw in wage_keywords):
                df[col] = pd.to_numeric(df[col], errors="coerce")

        self.stats.rows_cleaned += len(df)

        self.audit.log(
            action="CLEAN",
            sheet=sheet_name,
            detail=f"Cleaned: {rows_before} → {len(df)} rows",
            rows_affected=len(df),
            df=df,
        )

        return df

    # ----------------------------------------------------------
    # EMPLOYEE MASTER EXTRACTION
    # ----------------------------------------------------------

    def _extract_employee_master(self) -> pd.DataFrame:
        """
        Extract unique employee records from all parsed sheets
        to build a unified employee master.
        """
        name_col = "employee_name"
        id_col = "employee_id"

        records = []

        for sheet_key, df in self.sheet_data.items():
            if name_col not in df.columns:
                continue

            cols_to_keep = [c for c in (name_col, id_col, "uan_number", "pf_number", "site_location") if c in df.columns]
            if not cols_to_keep:
                continue

            subset = df[cols_to_keep].dropna(subset=[name_col]).copy()
            subset["_source_sheet"] = sheet_key
            records.append(subset)

        if not records:
            logger.warning("No employee data found in any sheet")
            return pd.DataFrame()

        master = pd.concat(records, ignore_index=True)
        master = master.dropna(subset=[name_col])
        master[name_col] = master[name_col].astype(str).str.upper().str.strip()

        # Keep first occurrence per employee (prefer records with ID)
        if id_col in master.columns:
            master["_has_id"] = master[id_col].notna().astype(int)
            master = master.sort_values("_has_id", ascending=False)
            master = master.drop_duplicates(subset=[name_col], keep="first")
            master = master.drop(columns=["_has_id"])
        else:
            master = master.drop_duplicates(subset=[name_col], keep="first")

        self.stats.employees_found = len(master)
        logger.info(f"Employee master: {len(master)} unique employees")

        self.audit.log(
            action="EMPLOYEE_MASTER",
            sheet="all",
            detail=f"Extracted {len(master)} unique employees",
            rows_affected=len(master),
            df=master,
        )

        return master.reset_index(drop=True)

    # ----------------------------------------------------------
    # SITE DETECTION
    # ----------------------------------------------------------

    def _detect_all_sites(self) -> List[str]:
        """
        Aggregate site/location names from:
          1. Sheet name hints
          2. Location columns in data
        """
        all_sites: set = set()

        # From sheet names
        for sheet_name in self.sheet_classifications:
            site = _detect_site_from_sheet_name(sheet_name)
            if site:
                all_sites.add(site)

        # From data columns
        for sheet_key, df in self.sheet_data.items():
            found = _detect_site_from_df(df)
            all_sites.update(found)

        self.site_list = sorted(all_sites)
        self.stats.sites_detected = len(self.site_list)

        logger.info(f"Detected {len(self.site_list)} sites: {self.site_list}")
        self.audit.log(
            action="SITE_DETECTION",
            sheet="all",
            detail=f"Found {len(self.site_list)} sites: {self.site_list}",
        )

        return self.site_list

    # ----------------------------------------------------------
    # ECR EXTRACTION (Electronic Challan cum Return)
    # ----------------------------------------------------------

    def _extract_ecr_data(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """
        Specific cleaning for ECR sheets — ensure all required
        PF account columns are numeric and validated.
        """
        ecr_cols = [
            "epf_contribution_ac01",
            "eps_contribution_ac02",
            "epf_admin_ac10",
            "edli_ac21",
            "epf_admin_ac22",
        ]

        for col in ecr_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Compute total employer contribution if columns exist
        present_ecr = [c for c in ecr_cols if c in df.columns]
        if len(present_ecr) >= 2:
            df["total_employer_remittance"] = df[present_ecr].sum(axis=1)
            logger.debug("Computed total_employer_remittance")

        self.audit.log(
            action="ECR_EXTRACT",
            sheet=sheet_name,
            detail=f"ECR columns processed: {present_ecr}",
            rows_affected=len(df),
            df=df,
        )

        return df

    # ----------------------------------------------------------
    # WAGE EXTRACTION
    # ----------------------------------------------------------

    def _extract_wage_summary(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Compute wage summary statistics from a wages DataFrame."""
        summary: Dict[str, Any] = {
            "sheet": sheet_name,
            "total_rows": len(df),
        }

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols:
            summary[f"{col}_sum"] = float(df[col].sum()) if not df[col].isna().all() else 0.0
            summary[f"{col}_mean"] = float(df[col].mean()) if not df[col].isna().all() else 0.0

        return summary

    # ----------------------------------------------------------
    # ATTENDANCE EXTRACTION
    # ----------------------------------------------------------

    def _extract_attendance(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """Validate and clean attendance data."""
        attendance_cols = [c for c in df.columns if any(k in c for k in ("days", "present", "attendance", "duty", "ot"))]

        for col in attendance_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Flag anomalies (negative days, > 31 days)
        if "days_worked" in df.columns:
            anomalies = df[(df["days_worked"] < 0) | (df["days_worked"] > 31)]
            if len(anomalies) > 0:
                logger.warning(f"Sheet '{sheet_name}': {len(anomalies)} attendance anomalies detected")
                self.stats.warnings += 1

        self.audit.log(
            action="ATTENDANCE_EXTRACT",
            sheet=sheet_name,
            detail=f"Attendance columns: {attendance_cols}",
            rows_affected=len(df),
            df=df,
        )

        return df

    # ----------------------------------------------------------
    # PARSE SINGLE SHEET
    # ----------------------------------------------------------

    def _parse_sheet(self, xls: pd.ExcelFile, sheet_name: str, category: str) -> Optional[pd.DataFrame]:
        """Full pipeline for a single sheet."""
        logger.info(f"{'='*60}")
        logger.info(f"Parsing sheet: '{sheet_name}' (category={category})")
        logger.info(f"{'='*60}")

        self.audit.log(action="PARSE_START", sheet=sheet_name, detail=f"Category={category}")

        # Step 1 — auto-header read
        df = self._read_with_auto_header(xls, sheet_name)
        if df.empty:
            return None

        self.stats.rows_read += len(df)

        # Step 2 — normalize columns
        df = self._normalize_columns(df)

        # Step 3 — clean
        df = self._clean_dataframe(df, sheet_name)

        # Step 4 — category-specific processing
        if category == "ecr":
            df = self._extract_ecr_data(df, sheet_name)
        elif category == "attendance":
            df = self._extract_attendance(df, sheet_name)
        elif category == "wages":
            wage_summary = self._extract_wage_summary(df, sheet_name)
            logger.info(f"Wage summary: {json.dumps(wage_summary, indent=2, default=str)}")

        # Step 5 — detect sites within this sheet
        sites_in_sheet = _detect_site_from_df(df)
        if sites_in_sheet:
            logger.info(f"Sites in '{sheet_name}': {sites_in_sheet}")

        self.stats.sheets_processed += 1
        self.audit.log(
            action="PARSE_COMPLETE",
            sheet=sheet_name,
            detail=f"Final shape={df.shape}",
            rows_affected=len(df),
            df=df,
        )

        return df

    # ----------------------------------------------------------
    # EXPORT
    # ----------------------------------------------------------

    def _save_csv(self, df: pd.DataFrame, name: str):
        path = self.output_dir / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"CSV saved → {path}")

    def _save_excel(self, data: Dict[str, pd.DataFrame], name: str):
        path = self.export_dir / f"{name}.xlsx"
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for sheet_key, df in data.items():
                safe_name = sheet_key[:31]  # Excel sheet name limit
                df.to_excel(writer, sheet_name=safe_name, index=False)
        logger.info(f"Excel saved → {path}")

    def _save_json_summary(self, summary: Dict[str, Any]):
        path = SUMMARY_DIR / f"parse_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)
        logger.info(f"JSON summary saved → {path}")

    # ----------------------------------------------------------
    # RUN — Main orchestration
    # ----------------------------------------------------------

    def run(self) -> Dict[str, Any]:
        """
        Execute the full parsing pipeline.

        Returns a summary dictionary with stats, sites, employees, and data.
        """
        logger.info("=" * 70)
        logger.info("SECURITY AI — EXCEL PARSER")
        logger.info(f"Input:  {self.input_path}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 70)

        self.audit.log(action="RUN_START", sheet="system", detail=f"File={self.input_path.name}")

        # Open workbook
        try:
            xls = pd.ExcelFile(self.input_path, engine="openpyxl")
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Failed to open Excel file: {e}")
            raise

        logger.info(f"Workbook contains {len(xls.sheet_names)} sheets: {xls.sheet_names}")

        # Step 1 — Discover and classify sheets
        sheet_map = self._discover_sheets(xls)
        logger.info(f"Classified sheets: {sheet_map}")

        # Step 2 — Parse every sheet (classified + unknown)
        all_sheets = set(xls.sheet_names)
        for sheet_name in all_sheets:
            category = self.sheet_classifications.get(sheet_name, "unknown")
            try:
                df = self._parse_sheet(xls, sheet_name, category)
                if df is not None and not df.empty:
                    self.sheet_data[sheet_name] = df
                    # Also store under category key if classified
                    if category != "unknown":
                        self.sheet_data[category] = df
            except Exception as e:
                self.stats.errors += 1
                logger.error(f"Error parsing sheet '{sheet_name}': {e}", exc_info=True)
                self.audit.log(
                    action="PARSE_ERROR",
                    sheet=sheet_name,
                    detail=str(e),
                )

        # Step 3 — Build employee master
        self.employee_master = self._extract_employee_master()

        # Step 4 — Detect all sites
        self._detect_all_sites()

        # Step 5 — Save outputs
        if not self.dry_run:
            # Individual CSVs
            for key, df in self.sheet_data.items():
                self._save_csv(df, key)

            # Combined Excel
            if self.sheet_data:
                self._save_excel(self.sheet_data, "all_parsed_data")

            # Employee master
            if self.employee_master is not None and not self.employee_master.empty:
                self._save_csv(self.employee_master, "employee_master")

            # Site list
            if self.site_list:
                site_df = pd.DataFrame({"site_location": self.site_list})
                self._save_csv(site_df, "site_list")

        # Step 6 — Build summary
        self.stats.finish()

        summary = {
            "meta": {
                "input_file": str(self.input_path),
                "input_size_bytes": self.input_path.stat().st_size,
                "parsed_at": datetime.now().isoformat(),
                "dry_run": self.dry_run,
                "parser_version": "2.0.0",
            },
            "runtime_stats": self.stats.summary(),
            "sheets_discovered": list(xls.sheet_names),
            "sheets_classified": self.sheet_classifications,
            "sheets_parsed": list(self.sheet_data.keys()),
            "sites": self.site_list,
            "employee_count": self.stats.employees_found,
            "data_shapes": {
                k: {"rows": len(v), "cols": len(v.columns), "columns": list(v.columns)}
                for k, v in self.sheet_data.items()
            },
            "audit_trail_count": len(self.audit.entries),
        }

        # Step 7 — Save summary and audit
        if not self.dry_run:
            self._save_json_summary(summary)
            audit_path = (
                SUMMARY_DIR / f"audit_trail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            self.audit.save(audit_path)

        # Final report
        logger.info("=" * 70)
        logger.info("PARSING COMPLETE")
        logger.info(f"  Sheets parsed:      {self.stats.sheets_processed}")
        logger.info(f"  Sheets skipped:     {self.stats.sheets_skipped}")
        logger.info(f"  Rows read:          {self.stats.rows_read}")
        logger.info(f"  Rows cleaned:       {self.stats.rows_cleaned}")
        logger.info(f"  Duplicates removed: {self.stats.rows_dropped_duplicate}")
        logger.info(f"  Employees found:    {self.stats.employees_found}")
        logger.info(f"  Sites detected:     {self.stats.sites_detected}")
        logger.info(f"  Columns normalized: {self.stats.columns_normalized}")
        logger.info(f"  Headers auto-det:   {self.stats.headers_auto_detected}")
        logger.info(f"  Errors:             {self.stats.errors}")
        logger.info(f"  Warnings:           {self.stats.warnings}")
        logger.info(f"  Elapsed:            {self.stats.elapsed}s")
        logger.info("=" * 70)

        return summary


# ============================================================
# CONVENIENCE FUNCTION (backward-compatible)
# ============================================================


def run(excel_path: str, **kwargs) -> Dict[str, Any]:
    """Backward-compatible entry point."""
    parser = ExcelParser(input_path=excel_path, **kwargs)
    return parser.run()


# ============================================================
# CLI ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    import argparse

    argp = argparse.ArgumentParser(
        description="Security AI — Excel Parser for PF Wages Reconciliation"
    )
    argp.add_argument(
        "file",
        nargs="?",
        default=str(RAW_DIR / "pf_wages_reconciliation.xlsx"),
        help="Path to the input Excel file",
    )
    argp.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse without writing output files",
    )
    argp.add_argument(
        "--no-dedup",
        action="store_true",
        help="Disable deduplication",
    )
    argp.add_argument(
        "--header-scan",
        type=int,
        default=15,
        help="Max rows to scan for auto header detection (default: 15)",
    )
    argp.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Custom output directory for CSVs",
    )

    args = argp.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else None

    parser = ExcelParser(
        input_path=args.file,
        output_dir=out_dir,
        dry_run=args.dry_run,
        deduplicate=not args.no_dedup,
        header_scan_rows=args.header_scan,
    )

    result = parser.run()

    print("\n" + json.dumps(result["runtime_stats"], indent=2))
