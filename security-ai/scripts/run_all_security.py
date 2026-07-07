# security-ai/scripts/run_all_security.py
"""
Production-Grade Security AI Pipeline Orchestrator
Security AI — Full Pipeline Execution, Monitoring & Recovery System

═══════════════════════════════════════════════════════════════════
 27 MODULES | 70+ FUNCTIONS | PARALLEL | RESUME | RETRY | DASHBOARD
═══════════════════════════════════════════════════════════════════

 MODULES:
  1.  Pipeline Health Check
  2.  Input Validation
  3.  Output Validation
  4.  Dependency Management (DAG)
  5.  Resume / Checkpoint
  6.  Skip Completed
  7.  Runtime Statistics
  8.  Progress Display
  9.  Error Recovery
  10. Retry Failed Pipelines
  11. Parallel Execution
  12. Client Support
  13. Multi-Month Processing
  14. Configuration File
  15. Pipeline Dashboard
  16. Pipeline Report
  17. Log Rotation
  18. Notifications
  19. Version Tracking
  20. Dry Run Mode
  21. Command Line Options
  22. Execution History
  23. Automatic Cleanup
  24. Integrity Verification
  25. Final Report Integration
  26. Graceful Shutdown & Signal Handling
  27. Concurrency Lock & Audit Trail
"""

import argparse
import json
import logging
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import warnings
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

warnings.filterwarnings("ignore")

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
LOG_DIR = BASE_DIR / "logs"
CHECKPOINT_DIR = BASE_DIR / "checkpoints"
HISTORY_DIR = BASE_DIR / "history"
CACHE_DIR = BASE_DIR / "cache"
CONFIG_DIR = BASE_DIR / "config"
DASHBOARD_DIR = BASE_DIR / "dashboard"
DATASETS_DIR = BASE_DIR / "datasets"
RECON_DIR = BASE_DIR / "reconciliation"
FRAUD_DIR = BASE_DIR / "fraud_reports"
RISK_DIR = BASE_DIR / "risk_reports"
OUTPUT_DIR = BASE_DIR / "outputs"
ANOMALY_DIR = BASE_DIR / "anomaly_reports"
SITE_DIR = BASE_DIR / "site_reports"
SUMMARY_DIR = BASE_DIR / "summaries"
EXPORT_DIR = BASE_DIR / "exports"
CLIENTS_DIR = BASE_DIR / "clients"
LOCK_DIR = BASE_DIR / ".locks"

ALL_DIRS = [
    LOG_DIR, CHECKPOINT_DIR, HISTORY_DIR, CACHE_DIR, CONFIG_DIR,
    DASHBOARD_DIR, DATASETS_DIR, RECON_DIR, FRAUD_DIR, RISK_DIR,
    OUTPUT_DIR, ANOMALY_DIR, SITE_DIR, SUMMARY_DIR, EXPORT_DIR,
    CLIENTS_DIR, LOCK_DIR,
]

for _d in ALL_DIRS:
    _d.mkdir(parents=True, exist_ok=True)


# ============================================================
# ENUMS & CONSTANTS
# ============================================================


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class PipelineStage(str, Enum):
    EXCEL_PARSER = "excel_parser.py"
    EMPLOYEE_MATCHING = "employee_matching_engine.py"
    PF_RECONCILIATION = "pf_reconciliation_engine.py"
    ESI_RECONCILIATION = "esi_reconciliation_engine.py"
    WAGE_ANOMALY = "wage_anomaly_detector.py"
    COMPLIANCE_RISK = "compliance_risk_scoring_engine.py"
    FRAUD_DETECTION = "fraud_detection_engine.py"
    SITE_PERFORMANCE = "site_performance_scoring_engine.py"
    FINAL_REPORT = "final_security_report.py"


# Default DAG — defines execution order and dependencies
DEFAULT_DAG: Dict[str, List[str]] = {
    "excel_parser.py": [],
    "employee_matching_engine.py": ["excel_parser.py"],
    "pf_reconciliation_engine.py": ["employee_matching_engine.py"],
    "esi_reconciliation_engine.py": ["employee_matching_engine.py"],
    "wage_anomaly_detector.py": ["employee_matching_engine.py"],
    "compliance_risk_scoring_engine.py": ["pf_reconciliation_engine.py", "esi_reconciliation_engine.py"],
    "fraud_detection_engine.py": ["wage_anomaly_detector.py", "employee_matching_engine.py"],
    "site_performance_scoring_engine.py": ["employee_matching_engine.py"],
    "final_security_report.py": [
        "pf_reconciliation_engine.py",
        "esi_reconciliation_engine.py",
        "wage_anomaly_detector.py",
        "compliance_risk_scoring_engine.py",
        "fraud_detection_engine.py",
        "site_performance_scoring_engine.py",
    ],
}

# Expected output files per pipeline
PIPELINE_OUTPUTS: Dict[str, List[str]] = {
    "excel_parser.py": [
        "datasets/guards_master.csv",
        "datasets/site_assignments.csv",
        "datasets/attendance.csv",
        "datasets/payroll.csv",
    ],
    "employee_matching_engine.py": [
        "datasets/site_assignments.csv",
    ],
    "pf_reconciliation_engine.py": [
        "reconciliation/pf_reconciliation_report.csv",
    ],
    "esi_reconciliation_engine.py": [
        "reconciliation/esi_reconciliation_report.csv",
    ],
    "wage_anomaly_detector.py": [
        "anomaly_reports/wage_anomaly_report.csv",
    ],
    "compliance_risk_scoring_engine.py": [
        "risk_reports/compliance_risk_report.csv",
    ],
    "fraud_detection_engine.py": [
        "fraud_reports/fraud_detection_report.csv",
    ],
    "site_performance_scoring_engine.py": [
        "site_reports/site_performance_scores.csv",
        "outputs/site_performance_scores.csv",
    ],
    "final_security_report.py": [
        "outputs/security_ai_final_report.csv",
        "summaries/security_ai_dashboard.json",
    ],
}

# Critical columns per output
EXPECTED_COLUMNS: Dict[str, Dict[str, List[str]]] = {
    "datasets/guards_master.csv": {"required": ["Guard_ID"]},
    "datasets/site_assignments.csv": {"required": ["Guard_ID", "Site_ID"]},
    "datasets/attendance.csv": {"required": ["Guard_ID"]},
    "reconciliation/pf_reconciliation_report.csv": {"required": []},
    "reconciliation/esi_reconciliation_report.csv": {"required": []},
    "anomaly_reports/wage_anomaly_report.csv": {"required": []},
}


# ============================================================
# MODULE 26 — GRACEFUL SHUTDOWN & SIGNAL HANDLING
# ============================================================


class ShutdownHandler:
    """Coordinate graceful shutdown across threads."""

    def __init__(self):
        self._shutdown_event = threading.Event()
        self._active_processes: List[subprocess.Popen] = []
        self._lock = threading.Lock()
        self._original_sigint = None
        self._original_sigterm = None

    @property
    def should_stop(self) -> bool:
        return self._shutdown_event.is_set()

    def request_shutdown(self, reason: str = "user request"):
        if not self._shutdown_event.is_set():
            self._shutdown_event.set()
            logging.getLogger("SecurityPipeline").warning(
                f"Shutdown requested: {reason}"
            )
            self._terminate_active_processes()

    def register_process(self, proc: subprocess.Popen):
        with self._lock:
            self._active_processes.append(proc)

    def unregister_process(self, proc: subprocess.Popen):
        with self._lock:
            try:
                self._active_processes.remove(proc)
            except ValueError:
                pass

    def _terminate_active_processes(self):
        with self._lock:
            for proc in self._active_processes:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                except Exception:
                    pass

    def install_signal_handlers(self):
        def _handler(signum, frame):
            name = signal.Signals(signum).name
            self.request_shutdown(f"received {name}")

        self._original_sigint = signal.signal(signal.SIGINT, _handler)
        self._original_sigterm = signal.signal(signal.SIGTERM, _handler)

    def restore_signal_handlers(self):
        if self._original_sigint:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm:
            signal.signal(signal.SIGTERM, self._original_sigterm)


shutdown_handler = ShutdownHandler()


# ============================================================
# MODULE 27 — CONCURRENCY LOCK & AUDIT TRAIL
# ============================================================


class PipelineLock:
    """File-based lock to prevent concurrent pipeline runs for the same client/month."""

    def __init__(self, lock_dir: Path, client: str, month: str):
        self._lock_file = lock_dir / f"pipeline_{client}_{month or 'default'}.lock"
        self._fd = None

    def acquire(self, timeout: float = 5.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                # O_CREAT | O_EXCL for atomic creation
                fd = os.open(
                    str(self._lock_file),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                os.write(fd, f"{os.getpid()}\n{datetime.now().isoformat()}\n".encode())
                os.close(fd)
                self._fd = fd
                return True
            except FileExistsError:
                # Check if the lock is stale
                try:
                    with open(self._lock_file) as f:
                        lines = f.readlines()
                        if len(lines) >= 2:
                            lock_time = datetime.fromisoformat(lines[1].strip())
                            if datetime.now() - lock_time > timedelta(hours=2):
                                self._lock_file.unlink(missing_ok=True)
                                continue
                except (ValueError, OSError):
                    pass
                time.sleep(0.5)
        return False

    def release(self):
        self._lock_file.unlink(missing_ok=True)


@dataclass
class AuditEntry:
    """Structured audit log entry."""
    timestamp: str = ""
    run_id: str = ""
    action: str = ""
    module: str = ""
    stage: str = ""
    detail: str = ""
    level: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditTrail:
    """Thread-safe audit trail writer."""

    def __init__(self, log_dir: Path, run_id: str):
        self._entries: List[AuditEntry] = []
        self._lock = threading.Lock()
        self._run_id = run_id
        self._log_path = log_dir / f"audit_{run_id}.jsonl"

    def log(
        self,
        action: str,
        module: str = "",
        stage: str = "",
        detail: str = "",
        level: str = "INFO",
    ):
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            run_id=self._run_id,
            action=action,
            module=module,
            stage=stage,
            detail=detail,
            level=level,
        )
        with self._lock:
            self._entries.append(entry)
            try:
                with open(self._log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry.to_dict(), default=str) + "\n")
            except OSError:
                pass

    def get_entries(self) -> List[AuditEntry]:
        with self._lock:
            return list(self._entries)

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            actions = defaultdict(int)
            for e in self._entries:
                actions[e.action] += 1
            return {
                "total_entries": len(self._entries),
                "actions": dict(actions),
                "first_entry": self._entries[0].timestamp if self._entries else None,
                "last_entry": self._entries[-1].timestamp if self._entries else None,
            }


# ============================================================
# CONFIGURATION DATA CLASSES
# ============================================================


@dataclass
class PipelineConfig:
    """Master pipeline configuration."""
    # Execution
    max_retries: int = 3
    retry_delay: int = 5
    stage_timeout: int = 600
    parallel: bool = False
    max_workers: int = 4
    continue_on_failure: bool = True
    skip_completed: bool = True
    dry_run: bool = False

    # Client / Month / Year
    client: str = "default"
    month: str = ""
    year: str = ""

    # Notifications
    notify_on_complete: bool = False
    notify_on_failure: bool = True
    notification_webhook: str = ""
    notification_email: str = ""

    # Cleanup
    cleanup_cache: bool = True
    cleanup_temp: bool = True
    max_log_age_days: int = 30
    max_history_entries: int = 100

    # Paths
    custom_config: str = ""

    # Safety
    lock_timeout: float = 10.0
    enable_lock: bool = True

    # Version
    pipeline_version: str = "9.0.0"
    engine_version: str = "10.0.0"


@dataclass
class StageResult:
    """Result of a single pipeline stage."""
    script: str = ""
    status: str = StageStatus.PENDING.value
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""
    rows_processed: int = 0
    output_files: List[str] = field(default_factory=list)
    output_rows: List[int] = field(default_factory=list)
    output_warnings: List[str] = field(default_factory=list)
    error_message: str = ""
    retry_count: int = 0
    skipped: bool = False
    cancelled: bool = False
    memory_peak_mb: float = 0.0


@dataclass
class ExecutionSummary:
    """Full execution summary."""
    run_id: str = ""
    client: str = ""
    month: str = ""
    year: str = ""
    pipeline_version: str = ""
    start_time: str = ""
    end_time: str = ""
    total_duration: float = 0.0
    total_stages: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    cancelled: int = 0
    retried: int = 0
    overall_status: str = ""
    stages: List[StageResult] = field(default_factory=list)
    audit_summary: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# MODULE 17 — LOG ROTATION
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(funcName)s:%(lineno)d | %(message)s"
)
LOG_DATE = "%Y-%m-%d %H:%M:%S"


def setup_rotating_logs(log_dir: Path) -> logging.Logger:
    """Production rotating log with daily files."""
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger("SecurityPipeline")
    root.setLevel(logging.DEBUG)

    if root.handlers:
        return root

    # Console
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(ch)

    # Main log — rotating
    fh = RotatingFileHandler(
        log_dir / "security_pipeline.log",
        maxBytes=20 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(fh)

    # Error log
    eh = RotatingFileHandler(
        log_dir / "security_pipeline_errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    eh.setLevel(logging.ERROR)
    eh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(eh)

    # Daily log
    today = datetime.now().strftime("%Y-%m-%d")
    dh = logging.FileHandler(
        log_dir / f"{today}.log",
        encoding="utf-8",
    )
    dh.setLevel(logging.DEBUG)
    dh.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    root.addHandler(dh)

    return root


logger = setup_rotating_logs(LOG_DIR)


def cleanup_old_logs(log_dir: Path, max_age_days: int = 30):
    """Remove log files older than max_age_days."""
    cutoff = datetime.now() - timedelta(days=max_age_days)
    removed = 0
    for f in log_dir.glob("????-??-??.log"):
        try:
            date_str = f.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            if file_date < cutoff:
                f.unlink()
                removed += 1
        except (ValueError, OSError):
            pass
    if removed:
        logger.info(f"Cleaned {removed} old log files")


# ============================================================
# MODULE 14 — CONFIGURATION FILE
# ============================================================


def _env_override(cfg: PipelineConfig) -> PipelineConfig:
    """Override config from environment variables."""
    env_map = {
        "SECURITY_AI_CLIENT": "client",
        "SECURITY_AI_MONTH": "month",
        "SECURITY_AI_YEAR": "year",
        "SECURITY_AI_MAX_RETRIES": ("max_retries", int),
        "SECURITY_AI_RETRY_DELAY": ("retry_delay", int),
        "SECURITY_AI_STAGE_TIMEOUT": ("stage_timeout", int),
        "SECURITY_AI_PARALLEL": ("parallel", lambda v: v.lower() in ("1", "true", "yes")),
        "SECURITY_AI_MAX_WORKERS": ("max_workers", int),
        "SECURITY_AI_WEBHOOK": "notification_webhook",
        "SECURITY_AI_DRY_RUN": ("dry_run", lambda v: v.lower() in ("1", "true", "yes")),
    }
    for env_key, attr in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            try:
                if isinstance(attr, tuple):
                    setattr(cfg, attr[0], attr[1](val))
                else:
                    setattr(cfg, attr, val)
            except (ValueError, AttributeError):
                pass
    return cfg


def load_configuration(config_path: Optional[Path] = None) -> PipelineConfig:
    cfg = PipelineConfig()

    # Try default config locations
    candidates = [
        config_path,
        CONFIG_DIR / "pipeline.json",
        CONFIG_DIR / "pipeline.yaml",
        CONFIG_DIR / "pipeline_config.json",
        BASE_DIR / "pipeline.json",
    ]

    loaded = False
    for path in candidates:
        if path and path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
                logger.info(f"Config loaded: {path}")
                loaded = True
                break
            except Exception as e:
                logger.warning(f"Config error ({path}): {e}")

    if not loaded:
        logger.debug("No config file found, using defaults")

    # Environment overrides take precedence
    cfg = _env_override(cfg)
    return cfg


def save_configuration(cfg: PipelineConfig):
    path = CONFIG_DIR / "pipeline.json"
    # Atomic write
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(CONFIG_DIR), suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(asdict(cfg), f, indent=2, default=str)
        shutil.move(tmp_path, str(path))
        logger.info(f"Config saved: {path}")
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


# ============================================================
# MODULE 21 — COMMAND LINE OPTIONS
# ============================================================


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Security AI Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_all_security.py                           # Default run
  python run_all_security.py --client client1          # Specific client
  python run_all_security.py --month June --year 2026  # Specific period
  python run_all_security.py --resume                  # Resume from checkpoint
  python run_all_security.py --dry-run                 # Validate without execution
  python run_all_security.py --parallel                # Parallel execution
  python run_all_security.py --skip-completed          # Skip already done stages
  python run_all_security.py --continue-on-failure     # Don't stop on errors
  python run_all_security.py --retry 5                 # 5 retries per stage
  python run_all_security.py --stages pf esi fraud     # Run specific stages
  python run_all_security.py --dashboard               # Show last run dashboard
  python run_all_security.py --history                 # Show execution history
  python run_all_security.py --export-history          # Export history to CSV
        """,
    )

    # Execution mode
    parser.add_argument("--client", default="default", help="Client name")
    parser.add_argument("--month", default="", help="Month (e.g. April, May)")
    parser.add_argument("--year", default="", help="Year (e.g. 2026)")

    # Pipeline control
    parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="Validate without executing")
    parser.add_argument("--parallel", action="store_true", help="Run independent stages in parallel")
    parser.add_argument("--skip-completed", action="store_true", help="Skip stages with existing output")
    parser.add_argument("--continue-on-failure", action="store_true", help="Continue if a stage fails")
    parser.add_argument("--retry", type=int, default=3, help="Max retries per stage")
    parser.add_argument("--retry-delay", type=int, default=5, help="Seconds between retries")
    parser.add_argument("--stage-timeout", type=int, default=600, help="Timeout per stage in seconds")

    # Stage selection
    parser.add_argument("--stages", nargs="*", help="Run specific stages (e.g. pf esi fraud)")
    parser.add_argument("--skip-stages", nargs="*", help="Skip specific stages")
    parser.add_argument("--only-final", action="store_true", help="Run only final report")

    # Information
    parser.add_argument("--dashboard", action="store_true", help="Show pipeline dashboard")
    parser.add_argument("--history", action="store_true", help="Show execution history")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--validate", action="store_true", help="Validate inputs only")
    parser.add_argument("--config", default=None, help="Custom config file path")
    parser.add_argument("--export-history", action="store_true", help="Export history to CSV")

    # Cleanup
    parser.add_argument("--cleanup", action="store_true", help="Cleanup cache and temp files")
    parser.add_argument("--reset-checkpoint", action="store_true", help="Clear checkpoint data")

    return parser.parse_args()


# ============================================================
# MODULE 19 — VERSION TRACKING
# ============================================================


def capture_version_information() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "pipeline_version": "9.0.0",
        "engine_version": "10.0.0",
        "execution_date": datetime.now().isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
        "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    }

    # Try git info
    for key, cmd in [
        ("git_commit", ["git", "rev-parse", "--short", "HEAD"]),
        ("git_branch", ["git", "branch", "--show-current"]),
    ]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, cwd=str(BASE_DIR),
                timeout=5,
            )
            info[key] = result.stdout.strip() if result.returncode == 0 else "unknown"
        except Exception:
            info[key] = "unknown"

    return info


# ============================================================
# MODULE 1 — PIPELINE HEALTH CHECK
# ============================================================


def validate_pipeline(dag: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
    """Check scripts exist, syntax is valid, dependencies exist."""
    results: Dict[str, Dict[str, Any]] = {}

    for script, deps in dag.items():
        path = SCRIPTS_DIR / script
        check: Dict[str, Any] = {
            "exists": path.exists(),
            "syntax_valid": False,
            "dependencies_met": True,
            "missing_deps": [],
            "file_size": 0,
        }

        if path.exists():
            check["file_size"] = path.stat().st_size

            # Syntax check
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(path)],
                    capture_output=True, text=True, timeout=10,
                )
                check["syntax_valid"] = result.returncode == 0
            except Exception:
                check["syntax_valid"] = False

            # Dependency check
            for dep in deps:
                dep_path = SCRIPTS_DIR / dep
                if not dep_path.exists():
                    check["dependencies_met"] = False
                    check["missing_deps"].append(dep)

        results[script] = check

    return results


# ============================================================
# MODULE 2 — INPUT VALIDATION
# ============================================================


def validate_inputs(
    config: PipelineConfig,
    dag: Dict[str, List[str]],
) -> Dict[str, Any]:
    """Verify all required inputs exist before execution."""
    report: Dict[str, Any] = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "files_checked": 0,
        "files_found": 0,
    }

    client = config.client
    month = config.month
    year = config.year

    # Check Excel source files
    excel_dir = BASE_DIR / "data"
    if client != "default":
        if month and year:
            excel_dir = CLIENTS_DIR / client / year / month
        elif month:
            excel_dir = CLIENTS_DIR / client / month
        else:
            excel_dir = CLIENTS_DIR / client

    excel_files = list(excel_dir.glob("*.xlsx")) + list(excel_dir.glob("*.xls"))
    if not excel_files:
        # Also check datasets
        if not any(DATASETS_DIR.glob("*.csv")):
            report["errors"].append("No input files found (Excel or CSV)")
            report["valid"] = False
        else:
            report["warnings"].append("No Excel files found, using existing CSVs")
    else:
        report["files_found"] = len(excel_files)

    # Check required directories
    for d in ALL_DIRS:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            report["warnings"].append(f"Created missing directory: {d.name}")

    # Check if first stage can run
    first_stage = "excel_parser.py"
    if first_stage in dag:
        path = SCRIPTS_DIR / first_stage
        if not path.exists():
            report["errors"].append(f"First stage missing: {first_stage}")
            report["valid"] = False

    report["files_checked"] = len(excel_files) + len(list(DATASETS_DIR.glob("*.csv")))
    return report


# ============================================================
# MODULE 3 — OUTPUT VALIDATION
# ============================================================


def validate_stage_outputs(script: str) -> Tuple[bool, List[str], Dict[str, int]]:
    """Validate outputs of a completed stage."""
    issues: List[str] = []
    output_rows: Dict[str, int] = {}
    expected = PIPELINE_OUTPUTS.get(script, [])

    if not expected:
        return True, issues, output_rows

    any_found = False
    for rel_path in expected:
        full_path = BASE_DIR / rel_path
        output_rows[rel_path] = 0

        if not full_path.exists():
            issues.append(f"Missing output: {rel_path}")
            continue

        any_found = True

        if full_path.stat().st_size == 0:
            issues.append(f"Empty output: {rel_path}")
            continue

        # CSV validation
        if full_path.suffix == ".csv":
            try:
                df, col_issues = _csv_check(full_path, rel_path)
                row_count = len(df) if df is not None else 0
                output_rows[rel_path] = row_count
                issues.extend(col_issues)
            except Exception as e:
                issues.append(f"Corrupted CSV {rel_path}: {e}")

    return any_found, issues, output_rows


def _csv_check(
    path: Path,
    rel_path: str,
) -> Tuple[Optional[Any], List[str]]:
    """Check CSV file validity and required columns. Returns (DataFrame_or_None, issues)."""
    issues: List[str] = []
    import pandas as pd

    encodings = ["utf-8-sig", "utf-8", "latin-1"]
    df = None

    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            return None, [f"Empty CSV: {rel_path}"]

    if df is None:
        return None, [f"Unreadable CSV: {rel_path}"]

    if df.empty:
        return df, [f"Zero rows in: {rel_path}"]

    # Column check
    col_req = EXPECTED_COLUMNS.get(rel_path, {}).get("required", [])
    if col_req:
        actual = set(c.lower().strip() for c in df.columns)
        for req in col_req:
            if req.lower() not in actual:
                issues.append(f"Missing column '{req}' in {rel_path}")

    return df, issues


# ============================================================
# MODULE 4 — DEPENDENCY MANAGEMENT
# ============================================================


def build_pipeline_graph(
    stages: Optional[List[str]] = None,
    skip_stages: Optional[List[str]] = None,
) -> Dict[str, List[str]]:
    """Build execution DAG from config or defaults."""
    dag = dict(DEFAULT_DAG)

    # Filter to specific stages
    if stages:
        expanded: Set[str] = set()
        for stage in stages:
            for key in dag:
                if stage.lower() in key.lower():
                    expanded.add(key)
                    for dep in dag[key]:
                        expanded.add(dep)

        filtered_dag = {k: v for k, v in dag.items() if k in expanded}
        for k in filtered_dag:
            filtered_dag[k] = [d for d in filtered_dag[k] if d in filtered_dag]
        dag = filtered_dag

    # Remove skipped stages
    if skip_stages:
        to_remove: Set[str] = set()
        for stage in skip_stages:
            for key in dag:
                if stage.lower() in key.lower():
                    to_remove.add(key)
        for key in to_remove:
            del dag[key]
        for k in dag:
            dag[k] = [d for d in dag[k] if d not in to_remove]

    return dag


def topological_sort(dag: Dict[str, List[str]]) -> List[str]:
    """Sort DAG into execution order."""
    visited: Set[str] = set()
    order: List[str] = []

    def _visit(node: str):
        if node in visited:
            return
        visited.add(node)
        for dep in dag.get(node, []):
            _visit(dep)
        order.append(node)

    for node in dag:
        _visit(node)

    return order


def get_parallel_groups(dag: Dict[str, List[str]]) -> List[List[str]]:
    """Group stages that can run in parallel."""
    groups: List[List[str]] = []
    remaining = set(dag.keys())
    completed: Set[str] = set()

    while remaining:
        ready = [
            node for node in remaining
            if all(d in completed for d in dag.get(node, []))
        ]

        if not ready:
            # Circular dependency fallback
            ready = [next(iter(remaining))]

        groups.append(sorted(ready))
        for r in ready:
            remaining.discard(r)
            completed.add(r)

    return groups


def detect_cycles(dag: Dict[str, List[str]]) -> List[List[str]]:
    """Detect cycles in the DAG. Returns list of cycle paths."""
    cycles: List[List[str]] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {n: WHITE for n in dag}
    parent: Dict[str, Optional[str]] = {n: None for n in dag}

    def _dfs(node: str):
        color[node] = GRAY
        for dep in dag.get(node, []):
            if dep not in color:
                continue
            if color[dep] == GRAY:
                # Reconstruct cycle
                cycle = [dep]
                cur = node
                while cur != dep:
                    cycle.append(cur)
                    cur = parent.get(cur)  # type: ignore
                    if cur is None:
                        break
                cycles.append(cycle)
            elif color[dep] == WHITE:
                parent[dep] = node
                _dfs(dep)
        color[node] = BLACK

    for node in dag:
        if color.get(node) == WHITE:
            _dfs(node)

    return cycles


# ============================================================
# MODULE 5 — RESUME / CHECKPOINT
# ============================================================


def get_checkpoint_path(config: PipelineConfig) -> Path:
    key = f"{config.client}_{config.month or 'default'}"
    return CHECKPOINT_DIR / f"checkpoint_{key}.json"


def save_checkpoint(config: PipelineConfig, completed: Set[str], results: List[StageResult]):
    """Atomically save checkpoint data."""
    path = get_checkpoint_path(config)
    data = {
        "timestamp": datetime.now().isoformat(),
        "client": config.client,
        "month": config.month,
        "year": config.year,
        "completed_stages": sorted(completed),
        "results": [asdict(r) for r in results],
    }

    # Atomic write: write to temp file, then rename
    fd, tmp_path = tempfile.mkstemp(
        dir=str(CHECKPOINT_DIR), suffix=".json.tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, default=str)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def load_checkpoint(config: PipelineConfig) -> Dict[str, Any]:
    path = get_checkpoint_path(config)
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Checkpoint load error: {e}")
        return {}


def clear_checkpoint(config: PipelineConfig):
    path = get_checkpoint_path(config)
    if path.exists():
        path.unlink()
        logger.info("Checkpoint cleared")


# ============================================================
# MODULE 6 — SKIP COMPLETED
# ============================================================


def should_skip_stage(
    script: str,
    config: PipelineConfig,
    completed_from_checkpoint: Set[str],
) -> Tuple[bool, str]:
    """Determine if a stage can be skipped."""
    if script in completed_from_checkpoint:
        return True, "completed in previous run"

    if not config.skip_completed:
        return False, ""

    # Check if outputs exist and are fresh
    expected = PIPELINE_OUTPUTS.get(script, [])
    if not expected:
        return False, ""

    all_exist = True
    for rel_path in expected:
        full_path = BASE_DIR / rel_path
        if not full_path.exists() or full_path.stat().st_size == 0:
            all_exist = False
            break

    if all_exist:
        return True, "outputs already exist"

    return False, ""


# ============================================================
# MODULE 7 — RUNTIME STATISTICS
# ============================================================


def collect_runtime_statistics(
    pid: int,
    start_time: float,
) -> Dict[str, Any]:
    """Collect runtime stats for a process."""
    stats: Dict[str, Any] = {
        "duration_seconds": round(time.time() - start_time, 2),
        "pid": pid,
        "memory_rss_mb": 0.0,
        "memory_vms_mb": 0.0,
        "cpu_percent": 0.0,
        "num_threads": 0,
    }

    try:
        import psutil
        if pid > 0:
            p = psutil.Process(pid)
            if p.is_running():
                mem = p.memory_info()
                stats["memory_rss_mb"] = round(mem.rss / (1024 * 1024), 2)
                stats["memory_vms_mb"] = round(mem.vms / (1024 * 1024), 2)
                stats["cpu_percent"] = p.cpu_percent(interval=0.1)
                stats["num_threads"] = p.num_threads()
    except ImportError:
        pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    except Exception:
        pass

    return stats


# ============================================================
# MODULE 8 — PROGRESS DISPLAY
# ============================================================

_STATUS_ICONS = {
    "passed": "\u2713",
    "failed": "\u2717",
    "skipped": "\u2298",
    "running": "\u25b6",
    "cancelled": "\u2297",
    "retrying": "\u21bb",
}


def show_progress(
    completed: int,
    total: int,
    current_stage: str = "",
    status: str = "",
):
    """Display progress bar."""
    if total == 0:
        return

    pct = completed / total
    bar_len = 30
    filled = int(bar_len * pct)
    bar = "\u2588" * filled + "\u2591" * (bar_len - filled)

    icon = _STATUS_ICONS.get(status, " ")

    line = f"\r  [{bar}] {completed}/{total} ({pct * 100:.0f}%) {icon} {current_stage}"
    sys.stdout.write(line)
    sys.stdout.flush()

    if completed == total:
        sys.stdout.write("\n")


# ============================================================
# MODULE 9 — ERROR RECOVERY
# ============================================================


def handle_pipeline_error(
    script: str,
    result: subprocess.CompletedProcess,
    elapsed: float,
) -> StageResult:
    """Handle a failed pipeline stage."""
    error_msg = result.stderr.strip()[-500:] if result.stderr else "Unknown error"

    stage_result = StageResult(
        script=script,
        status=StageStatus.FAILED.value,
        end_time=datetime.now().isoformat(),
        duration_seconds=elapsed,
        exit_code=result.returncode,
        stdout=result.stdout[-1000:] if result.stdout else "",
        stderr=error_msg,
        error_message=error_msg,
    )

    logger.error(f"Pipeline FAILED: {script}")
    logger.error(f"  Exit code: {result.returncode}")
    logger.error(f"  Error: {error_msg[:200]}")

    return stage_result


# ============================================================
# MODULE 10 — RETRY FAILED PIPELINES
# ============================================================


def retry_pipeline(
    script: str,
    config: PipelineConfig,
    max_retries: int = 3,
    audit: Optional[AuditTrail] = None,
) -> StageResult:
    """Run a pipeline with automatic retry."""
    for attempt in range(1, max_retries + 1):
        if shutdown_handler.should_stop:
            return StageResult(
                script=script,
                status=StageStatus.CANCELLED.value,
                cancelled=True,
                error_message="Cancelled: shutdown requested",
            )

        logger.info(f"Attempt {attempt}/{max_retries}: {script}")

        if attempt > 1:
            if audit:
                audit.log(
                    action="retry",
                    module="retry_pipeline",
                    stage=script,
                    detail=f"Attempt {attempt}/{max_retries}",
                    level="WARNING",
                )
            logger.info(f"Retrying in {config.retry_delay}s...")
            time.sleep(config.retry_delay)

        result = run_single_stage(script, config)
        result.retry_count = attempt - 1

        if result.status == StageStatus.PASSED.value:
            if attempt > 1:
                logger.info(f"Succeeded on attempt {attempt}: {script}")
            return result

        logger.warning(f"Attempt {attempt} failed: {script}")

    # All retries exhausted
    result.retry_count = max_retries
    logger.error(f"All {max_retries} attempts exhausted: {script}")
    return result


# ============================================================
# STAGE RUNNER
# ============================================================


def run_single_stage(script: str, config: PipelineConfig) -> StageResult:
    """Execute a single pipeline stage."""
    script_path = SCRIPTS_DIR / script
    result = StageResult(
        script=script,
        status=StageStatus.RUNNING.value,
        start_time=datetime.now().isoformat(),
    )

    if not script_path.exists():
        result.status = StageStatus.FAILED.value
        result.error_message = f"Script not found: {script_path}"
        return result

    if shutdown_handler.should_stop:
        result.status = StageStatus.CANCELLED.value
        result.cancelled = True
        result.error_message = "Cancelled before start: shutdown requested"
        return result

    cmd = [sys.executable, str(script_path)]

    # Pass client/month/year as arguments
    if config.client and config.client != "default":
        cmd.extend(["--client", config.client])
    if config.month:
        cmd.extend(["--month", config.month])
    if config.year:
        cmd.extend(["--year", config.year])

    start = time.time()
    proc = None

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(BASE_DIR),
        )
        shutdown_handler.register_process(proc)

        # Monitor memory in background while process runs
        peak_mem = [0.0]
        def _watch_mem():
            try:
                import psutil
                pp = psutil.Process(proc.pid)
                while pp.is_running():
                    try:
                        rss = pp.memory_info().rss / (1024 * 1024)
                        if rss > peak_mem[0]:
                            peak_mem[0] = rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    time.sleep(0.25)
            except Exception:
                pass
        mem_thread = threading.Thread(target=_watch_mem, daemon=True)
        mem_thread.start()

        try:
            stdout, stderr = proc.communicate(timeout=config.stage_timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            raise subprocess.TimeoutExpired(cmd, config.stage_timeout)
        finally:
            mem_thread.join(timeout=2)

        elapsed = round(time.time() - start, 2)
        result.memory_peak_mb = round(peak_mem[0], 1)

        if proc.returncode == 0:
            # Validate outputs
            valid, issues, output_rows = validate_stage_outputs(script)

            result.status = StageStatus.PASSED.value
            result.exit_code = 0
            result.stdout = stdout[-2000:] if stdout else ""
            result.output_files = list(output_rows.keys())
            result.output_rows = list(output_rows.values())
            result.output_warnings = issues
            result.rows_processed = sum(output_rows.values())
            result.duration_seconds = elapsed
            result.end_time = datetime.now().isoformat()

            if issues:
                logger.warning(f"Output warnings for {script}: {issues}")
        else:
            result = handle_pipeline_error(script, subprocess.CompletedProcess(
                cmd, proc.returncode, stdout, stderr
            ), elapsed)

    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - start, 2)
        result.status = StageStatus.FAILED.value
        result.error_message = f"Timeout after {elapsed}s (limit: {config.stage_timeout}s)"
        result.duration_seconds = elapsed
        result.end_time = datetime.now().isoformat()

    except Exception as e:
        elapsed = round(time.time() - start, 2)
        result.status = StageStatus.FAILED.value
        result.error_message = str(e)
        result.duration_seconds = elapsed
        result.end_time = datetime.now().isoformat()
        logger.error(f"Unexpected error running {script}: {e}")

    finally:
        if proc is not None:
            shutdown_handler.unregister_process(proc)

    return result


# ============================================================
# MODULE 11 — PARALLEL EXECUTION
# ============================================================


def run_parallel_group(
    scripts: List[str],
    config: PipelineConfig,
    audit: Optional[AuditTrail] = None,
) -> List[StageResult]:
    """Run a group of independent stages in parallel."""
    results: List[StageResult] = []

    if shutdown_handler.should_stop:
        for script in scripts:
            results.append(StageResult(
                script=script,
                status=StageStatus.CANCELLED.value,
                cancelled=True,
            ))
        return results

    workers = min(len(scripts), config.max_workers)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for script in scripts:
            if shutdown_handler.should_stop:
                results.append(StageResult(
                    script=script,
                    status=StageStatus.CANCELLED.value,
                    cancelled=True,
                ))
                continue
            future = executor.submit(run_single_stage, script, config)
            futures[future] = script

        for future in as_completed(futures):
            script = futures[future]
            try:
                stage_result = future.result(timeout=config.stage_timeout + 60)
                results.append(stage_result)

                if stage_result.status == StageStatus.PASSED.value:
                    logger.info(
                        f"\u2713 {script} ({stage_result.duration_seconds}s, "
                        f"{stage_result.rows_processed} rows)"
                    )
                elif stage_result.status == StageStatus.CANCELLED.value:
                    logger.warning(f"\u2297 {script}: cancelled")
                else:
                    logger.error(f"\u2717 {script}: {stage_result.error_message[:100]}")

            except Exception as e:
                results.append(StageResult(
                    script=script,
                    status=StageStatus.FAILED.value,
                    error_message=str(e),
                ))

    return results


# ============================================================
# MODULE 12 & 13 — CLIENT & MONTH SUPPORT
# ============================================================


def run_client_pipeline(
    client: str,
    months: Optional[List[str]] = None,
    base_config: Optional[PipelineConfig] = None,
) -> Dict[str, ExecutionSummary]:
    """Run pipeline for a specific client, optionally across months."""
    cfg = base_config or PipelineConfig()
    cfg.client = client

    results: Dict[str, ExecutionSummary] = {}

    if not months:
        months = [""]  # Single run

    for month in months:
        if shutdown_handler.should_stop:
            logger.warning("Shutdown requested, stopping multi-month processing")
            break

        cfg.month = month
        run_id = f"{client}_{month or 'default'}_{datetime.now().strftime('%H%M%S')}"
        logger.info(f"Running client={client}, month={month or 'current'}")

        summary = execute_pipeline(cfg, run_id)
        results[month or "current"] = summary

    return results


def discover_months(client: str) -> List[str]:
    """Discover available months for a client."""
    client_dir = CLIENTS_DIR / client
    if not client_dir.exists():
        return []
    return sorted([d.name for d in client_dir.iterdir() if d.is_dir()])


# ============================================================
# MODULE 20 — DRY RUN
# ============================================================


def dry_run(
    dag: Dict[str, List[str]],
    config: PipelineConfig,
    audit: Optional[AuditTrail] = None,
) -> Dict[str, Any]:
    """Validate everything without executing."""
    logger.info("=" * 50)
    logger.info("DRY RUN MODE \u2014 No pipelines will execute")
    logger.info("=" * 50)

    report: Dict[str, Any] = {
        "mode": "dry_run",
        "timestamp": datetime.now().isoformat(),
        "client": config.client,
        "month": config.month,
        "year": config.year,
        "stages": {},
        "pipeline_health": {},
        "input_validation": {},
        "execution_order": [],
        "parallel_groups": [],
        "cycles": [],
    }

    # 0. Cycle detection
    cycles = detect_cycles(dag)
    if cycles:
        report["cycles"] = cycles
        for cycle in cycles:
            logger.error(f"  CYCLE DETECTED: {' -> '.join(cycle)}")

    # 1. Pipeline health
    health = validate_pipeline(dag)
    report["pipeline_health"] = health
    for script, check in health.items():
        icon = "\u2713" if check["exists"] and check["syntax_valid"] else "\u2717"
        logger.info(
            f"  {icon} {script}: exists={check['exists']}, "
            f"syntax={check['syntax_valid']}"
        )

    # 2. Input validation
    input_check = validate_inputs(config, dag)
    report["input_validation"] = input_check
    logger.info(f"  Inputs valid: {input_check['valid']}")
    for err in input_check["errors"]:
        logger.error(f"    Error: {err}")
    for warn in input_check["warnings"]:
        logger.warning(f"    Warning: {warn}")

    # 3. Execution order
    order = topological_sort(dag)
    report["execution_order"] = order
    logger.info(f"  Execution order: {' -> '.join(order)}")

    # 4. Parallel groups
    groups = get_parallel_groups(dag)
    report["parallel_groups"] = groups
    for i, group in enumerate(groups):
        logger.info(f"  Group {i + 1}: {', '.join(group)}")

    # 5. Per-stage analysis
    for script in order:
        stage_info: Dict[str, Any] = {
            "dependencies": dag.get(script, []),
            "expected_outputs": PIPELINE_OUTPUTS.get(script, []),
        }

        outputs_exist = []
        for out in PIPELINE_OUTPUTS.get(script, []):
            path = BASE_DIR / out
            outputs_exist.append({
                "path": out,
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0,
            })
        stage_info["output_status"] = outputs_exist

        would_skip, reason = should_skip_stage(script, config, set())
        stage_info["would_skip"] = would_skip
        stage_info["skip_reason"] = reason

        report["stages"][script] = stage_info
        skip_info = f" [SKIP: {reason}]" if would_skip else ""
        logger.info(
            f"  {script}: deps={len(dag.get(script, []))}, "
            f"outputs={len(outputs_exist)}{skip_info}"
        )

    if audit:
        audit.log(
            action="dry_run_complete",
            module="dry_run",
            detail=f"Stages: {len(order)}, Valid: {input_check['valid']}",
        )

    logger.info("=" * 50)
    logger.info("DRY RUN COMPLETE \u2014 No changes made")
    return report


# ============================================================
# MODULE 18 — NOTIFICATIONS
# ============================================================


def send_notification(
    summary: ExecutionSummary,
    config: PipelineConfig,
):
    """Send notification on completion/failure."""
    if not config.notify_on_complete and not config.notify_on_failure:
        return

    if config.notify_on_failure and summary.overall_status != "failed":
        return

    status_word = "COMPLETED" if summary.overall_status == "passed" else "FAILED"
    message = (
        f"Security AI Pipeline {status_word}\n"
        f"Client: {summary.client}\n"
        f"Month: {summary.month or 'current'}\n"
        f"Year: {summary.year or 'current'}\n"
        f"Duration: {summary.total_duration:.1f}s\n"
        f"Stages: {summary.passed}\u2713 {summary.failed}\u2717 {summary.skipped}\u2298\n"
        f"Run ID: {summary.run_id}"
    )

    # Webhook notification
    if config.notification_webhook:
        try:
            import urllib.request
            data = json.dumps({"text": message}).encode("utf-8")
            req = urllib.request.Request(
                config.notification_webhook,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
            logger.info("Webhook notification sent")
        except Exception as e:
            logger.warning(f"Webhook notification failed: {e}")

    # Log notification
    logger.info(f"NOTIFICATION: {message}")


# ============================================================
# MODULE 22 — EXECUTION HISTORY
# ============================================================


def save_execution_history(summary: ExecutionSummary):
    """Atomically append to execution history file."""
    path = HISTORY_DIR / "execution_history.json"

    history: List[Dict] = []
    if path.exists():
        try:
            with open(path) as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(asdict(summary))
    history = history[-100:]

    # Atomic write
    fd, tmp_path = tempfile.mkstemp(dir=str(HISTORY_DIR), suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(history, f, indent=2, default=str)
        shutil.move(tmp_path, str(path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def load_execution_history() -> List[Dict]:
    path = HISTORY_DIR / "execution_history.json"
    if not path.exists():
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []


def export_history_to_csv() -> Optional[Path]:
    """Export execution history to CSV format."""
    history = load_execution_history()
    if not history:
        logger.warning("No execution history to export")
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = EXPORT_DIR / f"execution_history_{ts}.csv"

    rows = []
    for entry in history:
        for stage in entry.get("stages", []):
            rows.append({
                "Run_ID": entry.get("run_id", ""),
                "Client": entry.get("client", ""),
                "Month": entry.get("month", ""),
                "Year": entry.get("year", ""),
                "Pipeline_Version": entry.get("pipeline_version", ""),
                "Overall_Status": entry.get("overall_status", ""),
                "Total_Duration": entry.get("total_duration", 0),
                "Script": stage.get("script", ""),
                "Stage_Status": stage.get("status", ""),
                "Duration": stage.get("duration_seconds", 0),
                "Rows_Processed": stage.get("rows_processed", 0),
                "Retry_Count": stage.get("retry_count", 0),
                "Error": stage.get("error_message", "")[:200],
            })

    import pandas as pd
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"History exported: {csv_path} ({len(rows)} rows)")
    return csv_path


# ============================================================
# MODULE 15 — PIPELINE DASHBOARD
# ============================================================


def generate_pipeline_dashboard(
    summary: ExecutionSummary,
    config: PipelineConfig,
) -> Dict[str, Any]:
    """Generate dashboard data from execution summary."""
    return {
        "run_id": summary.run_id,
        "client": summary.client,
        "month": summary.month,
        "year": summary.year,
        "overall_status": summary.overall_status,
        "total_duration": summary.total_duration,
        "start_time": summary.start_time,
        "end_time": summary.end_time,
        "stages": {
            "total": summary.total_stages,
            "passed": summary.passed,
            "failed": summary.failed,
            "skipped": summary.skipped,
            "cancelled": summary.cancelled,
            "retried": summary.retried,
        },
        "stage_details": [
            {
                "script": s.script,
                "status": s.status,
                "duration": s.duration_seconds,
                "rows": s.rows_processed,
                "retries": s.retry_count,
                "memory_mb": s.memory_peak_mb,
                "error": s.error_message[:100] if s.error_message else "",
                "warnings": s.output_warnings,
            }
            for s in summary.stages
        ],
        "audit_summary": summary.audit_summary,
        "version": capture_version_information(),
    }


def display_dashboard(dashboard: Dict[str, Any]):
    """Pretty-print the dashboard."""
    print("\n" + "=" * 70)
    print("  SECURITY AI PIPELINE DASHBOARD")
    print("=" * 70)
    print(f"  Run ID:      {dashboard.get('run_id', 'N/A')}")
    print(f"  Client:      {dashboard.get('client', 'N/A')}")
    month = dashboard.get('month', 'current')
    year = dashboard.get('year', '')
    period = f"{month} {year}".strip() if month or year else "current"
    print(f"  Period:      {period}")
    print(f"  Status:      {dashboard.get('overall_status', 'N/A').upper()}")
    print(f"  Duration:    {dashboard.get('total_duration', 0):.1f}s")
    print("-" * 70)

    stages = dashboard.get("stages", {})
    print(f"  Total:       {stages.get('total', 0)}")
    print(f"  Passed:      {stages.get('passed', 0)}")
    print(f"  Failed:      {stages.get('failed', 0)}")
    print(f"  Skipped:     {stages.get('skipped', 0)}")
    print(f"  Cancelled:   {stages.get('cancelled', 0)}")
    print(f"  Retried:     {stages.get('retried', 0)}")
    print("-" * 70)

    print(f"  {'STAGE':<42} {'STATUS':<10} {'TIME':>8} {'ROWS':>8} {'MEM':>8}")
    print("  " + "-" * 76)

    for detail in dashboard.get("stage_details", []):
        icon = _STATUS_ICONS.get(detail["status"], " ")
        mem = f"{detail.get('memory_mb', 0):.0f}M" if detail.get("memory_mb", 0) > 0 else "-"
        print(
            f"  {icon} {detail['script']:<40} {detail['status']:<10} "
            f"{detail['duration']:>6.1f}s {detail['rows']:>7} {mem:>8}"
        )
        if detail.get("error"):
            print(f"    \u2514\u2500 {detail['error']}")
        if detail.get("warnings"):
            for w in detail["warnings"][:3]:
                print(f"    \u26a0 {w}")

    print("=" * 70 + "\n")


# ============================================================
# MODULE 16 — PIPELINE REPORT
# ============================================================


def generate_pipeline_report(
    summary: ExecutionSummary,
    dashboard: Dict[str, Any],
):
    """Save pipeline execution report."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV report
    csv_path = OUTPUT_DIR / "pipeline_summary.csv"
    rows = []
    for s in summary.stages:
        rows.append({
            "Run_ID": summary.run_id,
            "Script": s.script,
            "Status": s.status,
            "Duration_Seconds": s.duration_seconds,
            "Rows_Processed": s.rows_processed,
            "Retry_Count": s.retry_count,
            "Exit_Code": s.exit_code,
            "Memory_Peak_MB": s.memory_peak_mb,
            "Error": s.error_message[:200] if s.error_message else "",
        })

    import pandas as pd
    pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Report \u2192 {csv_path}")

    # JSON report
    json_path = SUMMARY_DIR / f"pipeline_report_{ts}.json"
    # Atomic write
    fd, tmp_path = tempfile.mkstemp(dir=str(SUMMARY_DIR), suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(dashboard, f, indent=2, default=str)
        shutil.move(tmp_path, str(json_path))
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise
    logger.info(f"Report \u2192 {json_path}")


# ============================================================
# MODULE 23 — AUTOMATIC CLEANUP
# ============================================================


def cleanup_workspace(config: PipelineConfig):
    """Clean temporary files, cache, and old logs."""
    cleaned = 0

    # Cache
    if config.cleanup_cache and CACHE_DIR.exists():
        for f in CACHE_DIR.iterdir():
            try:
                if f.is_file():
                    f.unlink()
                    cleaned += 1
            except OSError:
                pass

    # Temp files in outputs
    if config.cleanup_temp:
        for d in [OUTPUT_DIR, RECON_DIR, CHECKPOINT_DIR]:
            for pattern in ("*.tmp", "*.json.tmp"):
                for f in d.glob(pattern):
                    try:
                        f.unlink()
                        cleaned += 1
                    except OSError:
                        pass

    # Old logs
    cleanup_old_logs(LOG_DIR, config.max_log_age_days)

    # Old history
    history_path = HISTORY_DIR / "execution_history.json"
    if history_path.exists():
        try:
            with open(history_path) as f:
                history = json.load(f)
            if len(history) > config.max_history_entries:
                history = history[-config.max_history_entries:]
                fd, tmp_path = tempfile.mkstemp(dir=str(HISTORY_DIR), suffix=".json.tmp")
                try:
                    with os.fdopen(fd, "w") as f:
                        json.dump(history, f, indent=2, default=str)
                    shutil.move(tmp_path, str(history_path))
                except Exception:
                    Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass

    # Old audit files (keep last 50)
    audit_files = sorted(LOG_DIR.glob("audit_*.jsonl"), key=lambda p: p.name)
    if len(audit_files) > 50:
        for old_file in audit_files[:-50]:
            try:
                old_file.unlink()
                cleaned += 1
            except OSError:
                pass

    # Stale lock files
    for lock_file in LOCK_DIR.glob("*.lock"):
        try:
            with open(lock_file) as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    lock_time = datetime.fromisoformat(lines[1].strip())
                    if datetime.now() - lock_time > timedelta(hours=2):
                        lock_file.unlink()
                        cleaned += 1
        except (ValueError, OSError):
            try:
                lock_file.unlink()
                cleaned += 1
            except OSError:
                pass

    if cleaned:
        logger.info(f"Cleanup: removed {cleaned} stale files")


# ============================================================
# MODULE 24 — INTEGRITY VERIFICATION
# ============================================================


def verify_dataset_integrity(dag: Dict[str, List[str]]) -> Dict[str, Any]:
    """Verify integrity of all datasets between pipeline stages."""
    report: Dict[str, Any] = {
        "valid": True,
        "checks": [],
        "errors": [],
        "warnings": [],
    }

    for script, outputs in PIPELINE_OUTPUTS.items():
        for rel_path in outputs:
            full_path = BASE_DIR / rel_path
            check: Dict[str, Any] = {
                "file": rel_path,
                "pipeline": script,
                "exists": full_path.exists(),
                "non_empty": False,
                "readable": False,
                "no_duplicates": True,
                "row_count": 0,
                "file_size": 0,
                "last_modified": None,
            }

            if full_path.exists():
                stat = full_path.stat()
                check["file_size"] = stat.st_size
                check["last_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()

            if full_path.exists() and full_path.suffix == ".csv" and stat.st_size > 0:
                try:
                    import pandas as pd
                    df = pd.read_csv(full_path, encoding="utf-8-sig")
                    check["non_empty"] = len(df) > 0
                    check["readable"] = True
                    check["row_count"] = len(df)

                    # Check for duplicate rows
                    dups = int(df.duplicated().sum())
                    if dups > 0:
                        check["no_duplicates"] = False
                        report["warnings"].append(
                            f"{rel_path}: {dups} duplicate rows"
                        )

                    # Check for all-null columns
                    null_cols = [c for c in df.columns if df[c].isna().all()]
                    if null_cols:
                        report["warnings"].append(
                            f"{rel_path}: all-null columns: {null_cols}"
                        )

                except Exception as e:
                    check["readable"] = False
                    report["errors"].append(f"{rel_path}: read error: {e}")
                    report["valid"] = False

            report["checks"].append(check)

    return report


# ============================================================
# MODULE 25 — FINAL REPORT INTEGRATION
# ============================================================


def run_final_report(config: PipelineConfig, audit: Optional[AuditTrail] = None) -> bool:
    """Execute final_security_report.py after all pipelines."""
    logger.info("Running Final Security Report Integration...")

    script = "final_security_report.py"
    script_path = SCRIPTS_DIR / script

    if not script_path.exists():
        logger.warning(f"Final report script not found: {script_path}")
        return False

    result = retry_pipeline(script, config, max_retries=2, audit=audit)

    if result.status == StageStatus.PASSED.value:
        logger.info("Final Security Report generated successfully")
        if audit:
            audit.log(
                action="final_report_success",
                module="final_report",
                stage=script,
                detail=f"Duration: {result.duration_seconds}s",
            )
        return True
    else:
        logger.error(f"Final Security Report failed: {result.error_message[:200]}")
        if audit:
            audit.log(
                action="final_report_failed",
                module="final_report",
                stage=script,
                detail=result.error_message[:200],
                level="ERROR",
            )
        return False


# ============================================================
# PIPELINE EXECUTION ENGINE
# ============================================================


def execute_pipeline(
    config: PipelineConfig,
    run_id: Optional[str] = None,
) -> ExecutionSummary:
    """Main pipeline execution engine."""
    if run_id is None:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_id = f"{config.client}_{config.month or 'default'}_{ts}"

    # Initialize audit trail
    audit = AuditTrail(LOG_DIR, run_id)
    audit.log(
        action="pipeline_start",
        module="orchestrator",
        detail=f"client={config.client}, month={config.month}, parallel={config.parallel}",
    )

    logger.info("=" * 70)
    logger.info("SECURITY AI PIPELINE ORCHESTRATOR")
    logger.info(f"  Run ID:  {run_id}")
    logger.info(f"  Client:  {config.client}")
    period_parts = []
    if config.month:
        period_parts.append(config.month)
    if config.year:
        period_parts.append(config.year)
    logger.info(f"  Period:  {' '.join(period_parts) or 'current'}")
    logger.info(f"  Version: {config.pipeline_version}")
    logger.info(f"  Mode:    {'DRY RUN' if config.dry_run else 'LIVE'}")
    logger.info("=" * 70)

    # Install signal handlers
    shutdown_handler.install_signal_handlers()

    total_start = time.time()
    pipeline_start_iso = datetime.now().isoformat()

    # Build DAG
    dag = build_pipeline_graph()
    execution_order = topological_sort(dag)
    parallel_groups = get_parallel_groups(dag)

    # Cycle check
    cycles = detect_cycles(dag)
    if cycles:
        logger.error(f"CYCLES DETECTED IN DAG: {cycles}")
        audit.log(
            action="cycle_detected",
            module="dag",
            detail=str(cycles),
            level="ERROR",
        )
        return ExecutionSummary(
            run_id=run_id,
            client=config.client,
            month=config.month,
            year=config.year,
            pipeline_version=config.pipeline_version,
            start_time=pipeline_start_iso,
            end_time=datetime.now().isoformat(),
            total_duration=round(time.time() - total_start, 2),
            overall_status="failed",
        )

    logger.info(f"Pipeline DAG: {len(dag)} stages, {len(parallel_groups)} groups")
    for i, group in enumerate(parallel_groups):
        logger.info(f"  Group {i + 1}: {', '.join(group)}")

    # ── Phase 1: Pre-flight checks ──
    logger.info("\nPHASE 1: PRE-FLIGHT CHECKS")

    health = validate_pipeline(dag)
    health_issues = [
        s for s, h in health.items()
        if not h["exists"] or not h["syntax_valid"]
    ]
    if health_issues:
        logger.error(f"Pipeline health issues: {health_issues}")
        for s in health_issues:
            h = health[s]
            if not h["exists"]:
                logger.error(f"  \u2717 {s}: script not found")
            if not h["syntax_valid"]:
                logger.error(f"  \u2717 {s}: syntax error")
        audit.log(
            action="health_check_failed",
            module="health_check",
            detail=f"Issues: {health_issues}",
            level="ERROR",
        )

    input_check = validate_inputs(config, dag)
    if not input_check["valid"]:
        logger.error("Input validation FAILED:")
        for err in input_check["errors"]:
            logger.error(f"  \u2717 {err}")
        audit.log(
            action="input_validation_failed",
            module="input_validation",
            detail=f"Errors: {input_check['errors']}",
            level="ERROR",
        )
    for warn in input_check["warnings"]:
        logger.warning(f"  \u26a0 {warn}")

    integrity = verify_dataset_integrity(dag)
    for err in integrity["errors"]:
        logger.error(f"  Integrity: {err}")

    # Dry run stops here
    if config.dry_run:
        dry_report = dry_run(dag, config, audit)
        audit.log(action="dry_run_complete", module="orchestrator")
        shutdown_handler.restore_signal_handlers()
        return ExecutionSummary(
            run_id=run_id,
            client=config.client,
            month=config.month,
            year=config.year,
            pipeline_version=config.pipeline_version,
            start_time=pipeline_start_iso,
            end_time=datetime.now().isoformat(),
            total_duration=round(time.time() - total_start, 2),
            total_stages=len(execution_order),
            overall_status="dry_run",
            audit_summary=audit.get_summary(),
        )

    # ── Phase 2: Acquire lock ──
    pipeline_lock = PipelineLock(LOCK_DIR, config.client, config.month)
    lock_acquired = False

    if config.enable_lock:
        lock_acquired = pipeline_lock.acquire(timeout=config.lock_timeout)
        if not lock_acquired:
            logger.error("Could not acquire pipeline lock — another run may be active")
            audit.log(
                action="lock_failed",
                module="lock",
                detail="Could not acquire lock",
                level="ERROR",
            )
            shutdown_handler.restore_signal_handlers()
            return ExecutionSummary(
                run_id=run_id,
                client=config.client,
                month=config.month,
                year=config.year,
                pipeline_version=config.pipeline_version,
                start_time=pipeline_start_iso,
                end_time=datetime.now().isoformat(),
                total_duration=round(time.time() - total_start, 2),
                overall_status="failed",
                audit_summary=audit.get_summary(),
            )
        audit.log(action="lock_acquired", module="lock")

    try:
        return _execute_pipeline_inner(
            config=config,
            run_id=run_id,
            dag=dag,
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            audit=audit,
            total_start=total_start,
            pipeline_start_iso=pipeline_start_iso,
        )
    finally:
        if lock_acquired:
            pipeline_lock.release()
            audit.log(action="lock_released", module="lock")
        shutdown_handler.restore_signal_handlers()


def _execute_pipeline_inner(
    config: PipelineConfig,
    run_id: str,
    dag: Dict[str, List[str]],
    execution_order: List[str],
    parallel_groups: List[List[str]],
    audit: AuditTrail,
    total_start: float,
    pipeline_start_iso: str,
) -> ExecutionSummary:
    """Inner execution logic (separated for clean lock handling)."""

    # ── Phase 3: Load checkpoint ──
    completed_from_checkpoint: Set[str] = set()
    if config.skip_completed:
        checkpoint = load_checkpoint(config)
        if checkpoint.get("completed_stages"):
            completed_from_checkpoint = set(checkpoint["completed_stages"])
            logger.info(
                f"Resuming from checkpoint: "
                f"{len(completed_from_checkpoint)} stages completed"
            )
            audit.log(
                action="checkpoint_loaded",
                module="checkpoint",
                detail=f"Stages: {sorted(completed_from_checkpoint)}",
            )

    # ── Phase 4: Execute stages ──
    logger.info("\nPHASE 2: PIPELINE EXECUTION")
    audit.log(action="execution_start", module="orchestrator")

    all_results: List[StageResult] = []
    completed_stages: Set[str] = set()
    total_stages = len(execution_order)
    completed_count = 0
    failed_count = 0
    cancelled_count = 0

    for group_idx, group in enumerate(parallel_groups):
        if shutdown_handler.should_stop:
            logger.warning("Shutdown requested \u2014 cancelling remaining stages")
            for script in group:
                if script not in completed_stages:
                    all_results.append(StageResult(
                        script=script,
                        status=StageStatus.CANCELLED.value,
                        cancelled=True,
                    ))
                    cancelled_count += 1
                    completed_count += 1
            continue

        logger.info(
            f"\n  --- Group {group_idx + 1}/{len(parallel_groups)}: "
            f"{', '.join(group)} ---"
        )

        if config.parallel and len(group) > 1:
            # Parallel execution within group
            to_run: List[str] = []
            for script in group:
                skip, reason = should_skip_stage(
                    script, config, completed_from_checkpoint
                )
                if skip:
                    sr = StageResult(
                        script=script,
                        status=StageStatus.SKIPPED.value,
                        skipped=True,
                    )
                    all_results.append(sr)
                    completed_stages.add(script)
                    completed_count += 1
                    show_progress(completed_count, total_stages, script, "skipped")
                    logger.info(f"  \u2298 Skipping {script}: {reason}")
                    audit.log(
                        action="stage_skipped",
                        module="orchestrator",
                        stage=script,
                        detail=reason,
                    )
                else:
                    to_run.append(script)

            if to_run:
                group_results = run_parallel_group(to_run, config, audit)
                for sr in group_results:
                    # Replace with retry if failed
                    if sr.status == StageStatus.FAILED.value and config.max_retries > 0:
                        failed_count += 1
                        sr = retry_pipeline(sr.script, config, config.max_retries, audit)
                        if sr.status == StageStatus.PASSED.value:
                            failed_count -= 1

                    all_results.append(sr)

                    if sr.status == StageStatus.PASSED.value:
                        completed_stages.add(sr.script)
                        completed_count += 1
                        show_progress(
                            completed_count, total_stages, sr.script, "passed"
                        )
                        save_checkpoint(config, completed_stages, all_results)
                        audit.log(
                            action="stage_passed",
                            module="orchestrator",
                            stage=sr.script,
                            detail=f"{sr.duration_seconds}s, {sr.rows_processed} rows",
                        )
                    elif sr.status == StageStatus.CANCELLED.value:
                        cancelled_count += 1
                        completed_count += 1
                        show_progress(
                            completed_count, total_stages, sr.script, "cancelled"
                        )
                    else:
                        completed_count += 1
                        show_progress(
                            completed_count, total_stages, sr.script, "failed"
                        )
                        if not config.continue_on_failure:
                            logger.error(
                                "Stopping pipeline (continue_on_failure=False)"
                            )
                            break

        else:
            # Sequential execution
            for script in group:
                if shutdown_handler.should_stop:
                    all_results.append(StageResult(
                        script=script,
                        status=StageStatus.CANCELLED.value,
                        cancelled=True,
                    ))
                    cancelled_count += 1
                    completed_count += 1
                    continue

                skip, reason = should_skip_stage(
                    script, config, completed_from_checkpoint
                )
                if skip:
                    sr = StageResult(
                        script=script,
                        status=StageStatus.SKIPPED.value,
                        skipped=True,
                    )
                    all_results.append(sr)
                    completed_stages.add(script)
                    completed_count += 1
                    show_progress(completed_count, total_stages, script, "skipped")
                    logger.info(f"  \u2298 Skipping {script}: {reason}")
                    audit.log(
                        action="stage_skipped",
                        module="orchestrator",
                        stage=script,
                        detail=reason,
                    )
                    continue

                # Check dependencies
                deps = dag.get(script, [])
                missing_deps = [d for d in deps if d not in completed_stages]
                if missing_deps:
                    logger.error(
                        f"  \u2717 Cannot run {script}: "
                        f"missing deps {missing_deps}"
                    )
                    sr = StageResult(
                        script=script,
                        status=StageStatus.FAILED.value,
                        error_message=f"Missing dependencies: {missing_deps}",
                    )
                    all_results.append(sr)
                    failed_count += 1
                    completed_count += 1
                    show_progress(
                        completed_count, total_stages, script, "failed"
                    )
                    audit.log(
                        action="stage_dep_missing",
                        module="orchestrator",
                        stage=script,
                        detail=f"Missing: {missing_deps}",
                        level="ERROR",
                    )

                    if not config.continue_on_failure:
                        logger.error(
                            "Stopping pipeline (continue_on_failure=False)"
                        )
                        break
                    continue

                # Run with retry
                show_progress(completed_count, total_stages, script, "running")
                audit.log(
                    action="stage_start",
                    module="orchestrator",
                    stage=script,
                )

                sr = retry_pipeline(script, config, config.max_retries, audit)
                all_results.append(sr)

                if sr.status == StageStatus.PASSED.value:
                    completed_stages.add(script)
                    completed_count += 1
                    show_progress(completed_count, total_stages, script, "passed")
                    logger.info(
                        f"  \u2713 {script} ({sr.duration_seconds}s, "
                        f"{sr.rows_processed} rows)"
                    )
                    save_checkpoint(config, completed_stages, all_results)
                    audit.log(
                        action="stage_passed",
                        module="orchestrator",
                        stage=script,
                        detail=(
                            f"duration={sr.duration_seconds}s, "
                            f"rows={sr.rows_processed}, "
                            f"memory={sr.memory_peak_mb:.1f}MB"
                        ),
                    )
                elif sr.status == StageStatus.CANCELLED.value:
                    cancelled_count += 1
                    completed_count += 1
                    show_progress(
                        completed_count, total_stages, script, "cancelled"
                    )
                else:
                    failed_count += 1
                    completed_count += 1
                    show_progress(completed_count, total_stages, script, "failed")
                    audit.log(
                        action="stage_failed",
                        module="orchestrator",
                        stage=script,
                        detail=sr.error_message[:200],
                        level="ERROR",
                    )
                    if not config.continue_on_failure:
                        logger.error(
                            "Stopping pipeline (continue_on_failure=False)"
                        )
                        break

    # ── Phase 5: Final report (only if not already run in DAG) ──
    logger.info("\nPHASE 3: FINAL REPORT")

    # Check if final_security_report.py was already part of the DAG execution
    final_script = "final_security_report.py"
    already_ran = any(
        r.script == final_script and r.status in (StageStatus.PASSED.value, StageStatus.SKIPPED.value)
        for r in all_results
    )

    if not already_ran:
        final_success = run_final_report(config, audit)
        if final_success:
            all_results.append(StageResult(
                script=final_script,
                status=StageStatus.PASSED.value,
                duration_seconds=0,
            ))
        else:
            all_results.append(StageResult(
                script=final_script,
                status=StageStatus.FAILED.value,
                error_message="Final report generation failed",
            ))
            failed_count += 1
    else:
        logger.info("Final report already executed in DAG \u2014 skipping duplicate run")

    # ── Build summary ──
    total_duration = round(time.time() - total_start, 2)
    passed = sum(
        1 for r in all_results if r.status == StageStatus.PASSED.value
    )
    failed = sum(
        1 for r in all_results if r.status == StageStatus.FAILED.value
    )
    skipped = sum(
        1 for r in all_results if r.status == StageStatus.SKIPPED.value
    )
    cancelled = sum(
        1 for r in all_results if r.status == StageStatus.CANCELLED.value
    )
    retried = sum(1 for r in all_results if r.retry_count > 0)

    if shutdown_handler.should_stop:
        overall_status = "cancelled"
    elif failed == 0:
        overall_status = "passed"
    elif passed > 0:
        overall_status = "partial"
    else:
        overall_status = "failed"

    summary = ExecutionSummary(
        run_id=run_id,
        client=config.client,
        month=config.month,
        year=config.year,
        pipeline_version=config.pipeline_version,
        start_time=pipeline_start_iso,
        end_time=datetime.now().isoformat(),
        total_duration=total_duration,
        total_stages=len(all_results),
        passed=passed,
        failed=failed,
        skipped=skipped,
        cancelled=cancelled,
        retried=retried,
        overall_status=overall_status,
        stages=all_results,
        audit_summary=audit.get_summary(),
    )

    # ── Phase 6: Post-execution ──
    dashboard = generate_pipeline_dashboard(summary, config)
    display_dashboard(dashboard)

    generate_pipeline_report(summary, dashboard)
    save_execution_history(summary)
    send_notification(summary, config)

    if config.cleanup_cache or config.cleanup_temp:
        cleanup_workspace(config)

    # Clear checkpoint on full success
    if failed == 0 and cancelled == 0:
        clear_checkpoint(config)

    audit.log(
        action="pipeline_complete",
        module="orchestrator",
        detail=(
            f"status={overall_status}, duration={total_duration}s, "
            f"passed={passed}, failed={failed}, skipped={skipped}, "
            f"cancelled={cancelled}"
        ),
    )

    # ── Final log ──
    logger.info("=" * 70)
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info(f"  Run ID:     {run_id}")
    logger.info(f"  Duration:   {total_duration}s")
    logger.info(f"  Passed:     {passed}")
    logger.info(f"  Failed:     {failed}")
    logger.info(f"  Skipped:    {skipped}")
    logger.info(f"  Cancelled:  {cancelled}")
    logger.info(f"  Retried:    {retried}")
    logger.info(f"  Status:     {overall_status.upper()}")
    logger.info(f"  Audit Log:  {LOG_DIR / f'audit_{run_id}.jsonl'}")
    logger.info("=" * 70)

    return summary


# ============================================================
# BACKWARD-COMPATIBLE run_all()
# ============================================================


def run_script(script_name: str):
    """Backward-compatible single script runner."""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Pipeline not found: {script_path}")

    logger.info(f"Running: {script_name}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True,
        cwd=str(BASE_DIR),
    )
    elapsed = round(time.time() - start, 2)

    if result.returncode != 0:
        logger.error(f"Failed: {script_name}\n{result.stderr[-500:]}")
        raise Exception(f"Pipeline failed: {script_name}")

    logger.info(f"Completed: {script_name} ({elapsed}s)")


def run_all():
    """Backward-compatible full pipeline runner."""
    config = PipelineConfig()
    execute_pipeline(config)


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    args = parse_arguments()

    # ── Informational modes ──
    if args.dashboard:
        history = load_execution_history()
        if history:
            display_dashboard(history[-1])
        else:
            print("No execution history found.")
        sys.exit(0)

    if args.history:
        history = load_execution_history()
        if not history:
            print("No execution history found.")
        else:
            print(
                f"\n  {'RUN ID':<35} {'CLIENT':<12} {'MONTH':<10} "
                f"{'STATUS':<10} {'DURATION':>8}"
            )
            print("  " + "-" * 75)
            for entry in history[-20:]:
                print(
                    f"  {entry.get('run_id', 'N/A'):<35} "
                    f"{entry.get('client', 'N/A'):<12} "
                    f"{entry.get('month', 'N/A'):<10} "
                    f"{entry.get('overall_status', 'N/A'):<10} "
                    f"{entry.get('total_duration', 0):>6.1f}s"
                )
        sys.exit(0)

    if args.export_history:
        path = export_history_to_csv()
        if path:
            print(f"History exported to: {path}")
        sys.exit(0)

    if args.status:
        health = validate_pipeline(DEFAULT_DAG)
        pipeline_status = {}
        for script, outputs in PIPELINE_OUTPUTS.items():
            any_exist = any((BASE_DIR / o).exists() for o in outputs)
            pipeline_status[script] = "PASS" if any_exist else "MISSING"

        print("\n=== PIPELINE STATUS ===")
        for s, st in pipeline_status.items():
            icon = "\u2713" if st == "PASS" else "\u2717"
            print(f"  {icon} {s}: {st}")
        sys.exit(0)

    if args.validate:
        config = PipelineConfig()
        config.client = args.client
        config.month = args.month
        config.year = args.year
        input_check = validate_inputs(config, DEFAULT_DAG)
        integrity = verify_dataset_integrity(DEFAULT_DAG)
        print(f"\nInputs valid: {input_check['valid']}")
        print(f"Integrity: {integrity['valid']}")
        for e in input_check["errors"] + integrity["errors"]:
            print(f"  Error: {e}")
        sys.exit(0)

    if args.cleanup:
        cleanup_workspace(PipelineConfig())
        print("Workspace cleaned.")
        sys.exit(0)

    if args.reset_checkpoint:
        clear_checkpoint(PipelineConfig())
        print("Checkpoint cleared.")
        sys.exit(0)

    # ── Main execution ──
    config = load_configuration(Path(args.config) if args.config else None)
    config.client = args.client or config.client
    config.month = args.month or config.month
    config.year = args.year or config.year
    config.parallel = args.parallel or config.parallel
    config.dry_run = args.dry_run or config.dry_run
    config.skip_completed = args.skip_completed or config.skip_completed
    config.continue_on_failure = args.continue_on_failure or config.continue_on_failure
    config.max_retries = args.retry
    config.retry_delay = args.retry_delay
    config.stage_timeout = args.stage_timeout

    if args.only_final:
        config = PipelineConfig(
            client=config.client,
            month=config.month,
            year=config.year,
        )
        success = run_final_report(config)
        sys.exit(0 if success else 1)

    summary = execute_pipeline(config)

    exit_code = 0 if summary.overall_status in ("passed", "dry_run") else 1
    if summary.overall_status == "cancelled":
        exit_code = 130  # Standard SIGINT exit code

    sys.exit(exit_code)
