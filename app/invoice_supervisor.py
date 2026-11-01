"""Run the invoice preparation and extraction worker from a synced intake folder.

This is a local Windows supervisor. It polls the configured
OneDrive-synced folder, waits for stable files, prepares each document, and
invokes the existing one-invoice LM Studio worker. It never batches invoice
items and never removes source files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any


SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}
TASK_NAME = "DataHermetica-InvoiceEngine-Supervisor"


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read JSON configuration {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")
    return value


def root_from_args(value: str | None) -> Path:
    configured = value or os.environ.get("DATA_HERMETICA_INVOICE_ENGINE_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
    else:
        # Installed location is <engine-root>\app\invoice_supervisor.py.
        root = Path(__file__).resolve().parent.parent
    if not root.is_dir():
        raise RuntimeError(f"Invoice engine root does not exist: {root}")
    return root


def intake_from_config(config: dict[str, Any], cli_value: str | None) -> Path:
    selected = cli_value or config.get("intake_directory")
    if selected:
        return Path(str(selected)).expanduser().resolve()
    onedrive = os.environ.get("OneDriveCommercial")
    if not onedrive:
        raise RuntimeError(
            "OneDriveCommercial is missing. Sign in to OneDrive or configure "
            "intake_directory in invoice_supervisor_config.json."
        )
    return (Path(onedrive) / "InvoiceIntake" / "Incoming").resolve()


def setup_logging(root: Path, config: dict[str, Any]) -> logging.Logger:
    log_path = root / "logs" / "invoice-supervisor.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    maximum_bytes = int(config.get("log_max_bytes", 5_000_000))
    backup_count = int(config.get("log_backup_count", 5))
    handler = RotatingFileHandler(
        log_path,
        maxBytes=maximum_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger = logging.getLogger("invoice_supervisor")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def open_state_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS supervisor_documents (
            document_sha256 TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            status TEXT NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            discovered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            worker_status TEXT,
            last_error TEXT
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS source_observations (
            source_file TEXT PRIMARY KEY,
            file_size INTEGER NOT NULL,
            modified_ns INTEGER NOT NULL,
            document_sha256 TEXT,
            status TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def take_single_instance_lock(root: Path):
    """Use an OS file lock so scheduled/task restarts cannot overlap."""
    lock_path = root / "state" / "supervisor.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def release_single_instance_lock(handle) -> None:
    if handle is None:
        return
    try:
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def stable_sha256(path: Path, stable_seconds: int, stable_checks: int) -> str:
    """Wait for size/mtime stability, then hash bytes and confirm no change."""
    previous: tuple[int, int] | None = None
    stable_count = 0
    deadline = time.monotonic() + max(stable_seconds * (stable_checks + 3), 90)

    while time.monotonic() < deadline:
        try:
            stat = path.stat()
            current = (stat.st_size, stat.st_mtime_ns)
            if stat.st_size <= 0:
                stable_count = 0
            elif current == previous:
                stable_count += 1
            else:
                stable_count = 0
                previous = current
            if stable_count >= stable_checks:
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                final = path.stat()
                if (final.st_size, final.st_mtime_ns) == current:
                    return digest.hexdigest()
                stable_count = 0
                previous = (final.st_size, final.st_mtime_ns)
        except (OSError, PermissionError):
            stable_count = 0
            previous = None
        time.sleep(max(stable_seconds, 1))

    raise TimeoutError(f"File did not become readable and stable: {path.name}")


def worker_job_status(database_path: Path, digest: str) -> str | None:
    if not database_path.is_file():
        return None
    try:
        with sqlite3.connect(database_path, timeout=10) as connection:
            row = connection.execute(
                "SELECT status FROM jobs WHERE document_sha256 = ?", (digest,)
            ).fetchone()
        return str(row[0]) if row else None
    except sqlite3.Error:
        return None


def lm_studio_model_ready(root: Path, config: dict[str, Any], logger: logging.Logger) -> bool:
    """Return True only when the configured model is visible through LM Studio."""
    engine_config_path = root / "config" / "engine_config.json"
    engine_config = json_file(engine_config_path)
    base_url = str(engine_config.get("lm_studio_base_url", "")).rstrip("/")
    model_id = str(engine_config.get("model", "")).strip()
    timeout = max(1, int(config.get("lm_studio_readiness_timeout_seconds", 5)))

    if not base_url or not model_id:
        raise RuntimeError(
            "engine_config.json must define lm_studio_base_url and model before "
            "the supervisor can process invoices."
        )

    request = urllib.request.Request(
        f"{base_url}/models",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        logger.info(
            "LM Studio is not ready; leaving intake files pending for the next scan. "
            "Cause: %s",
            type(exc).__name__,
        )
        return False

    model_ids = {
        str(model.get("id", ""))
        for model in payload.get("data", [])
        if isinstance(model, dict)
    }
    if model_id not in model_ids:
        logger.info(
            "Configured LM Studio model is not currently visible; "
            "leaving intake files pending for the next scan. model=%s",
            model_id,
        )
        return False

    logger.info("LM Studio endpoint and configured model are ready: %s", model_id)
    return True


def record_document(
    connection: sqlite3.Connection,
    digest: str,
    source: Path,
    status: str,
    *,
    worker_status: str | None = None,
    error: str | None = None,
    increment_attempt: bool = False,
) -> None:
    now = utc_now()
    with connection:
        connection.execute(
            """
            INSERT INTO supervisor_documents (
                document_sha256, source_file, status, attempt_count,
                discovered_at, updated_at, worker_status, last_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_sha256) DO UPDATE SET
                source_file=excluded.source_file,
                status=excluded.status,
                attempt_count=supervisor_documents.attempt_count + ?,
                updated_at=excluded.updated_at,
                worker_status=excluded.worker_status,
                last_error=excluded.last_error
            """,
            (
                digest,
                str(source),
                status,
                1 if increment_attempt else 0,
                now,
                now,
                worker_status,
                error,
                1 if increment_attempt else 0,
            ),
        )
        source_stat = source.stat()
        connection.execute(
            """
            INSERT INTO source_observations (
                source_file, file_size, modified_ns, document_sha256,
                status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_file) DO UPDATE SET
                file_size=excluded.file_size,
                modified_ns=excluded.modified_ns,
                document_sha256=excluded.document_sha256,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (
                str(source.resolve()),
                source_stat.st_size,
                source_stat.st_mtime_ns,
                digest,
                status,
                now,
            ),
        )


def known_path_unchanged(
    connection: sqlite3.Connection, source: Path, source_stat: os.stat_result
) -> bool:
    row = connection.execute(
        "SELECT file_size, modified_ns, status FROM source_observations WHERE source_file = ?",
        (str(source.resolve()),),
    ).fetchone()
    return bool(
        row
        and row["file_size"] == source_stat.st_size
        and row["modified_ns"] == source_stat.st_mtime_ns
        and row["status"] in {"COMPLETED", "REVIEW_REQUIRED", "FAILED", "DUPLICATE_COMPLETED"}
    )


def run_command(
    command: list[str], timeout: int, cwd: Path, logger: logging.Logger
) -> subprocess.CompletedProcess[str]:
    logger.info("Starting local command: %s", Path(command[0]).name)
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        env=os.environ.copy(),
    )
    if completed.stdout.strip():
        logger.info("Command summary: %s", completed.stdout.strip().replace("\n", " | ")[:2000])
    if completed.stderr.strip():
        logger.warning("Command diagnostic: %s", completed.stderr.strip().replace("\n", " | ")[:2000])
    if completed.returncode:
        logger.error("Command exited with status %s", completed.returncode)
    return completed


def process_one(
    source: Path,
    *,
    root: Path,
    intake: Path,
    config: dict[str, Any],
    connection: sqlite3.Connection,
    logger: logging.Logger,
) -> str:
    digest = stable_sha256(
        source,
        int(config.get("stable_check_interval_seconds", 5)),
        int(config.get("stable_checks", 2)),
    )
    logger.info("Stable input discovered: %s sha256=%s", source.name, digest)

    previous = connection.execute(
        "SELECT status FROM supervisor_documents WHERE document_sha256 = ?", (digest,)
    ).fetchone()
    worker_db = root / "state" / "jobs.db"
    existing_worker_status = worker_job_status(worker_db, digest)
    if existing_worker_status == "COMPLETED":
        record_document(connection, digest, source, "COMPLETED", worker_status="COMPLETED")
        logger.info("Already completed by invoice worker; skipping %s", source.name)
        return "COMPLETED"
    if existing_worker_status == "REVIEW_REQUIRED":
        record_document(
            connection, digest, source, "REVIEW_REQUIRED", worker_status="REVIEW_REQUIRED"
        )
        logger.warning("Worker has review-required state; skipping automatic retry: %s", source.name)
        return "REVIEW_REQUIRED"
    if previous and previous["status"] in {"REVIEW_REQUIRED", "FAILED"}:
        logger.warning("Supervisor state is %s; manual review is required: %s", previous["status"], source.name)
        return str(previous["status"])
    if previous and previous["status"] in {"COMPLETED", "DUPLICATE_COMPLETED"}:
        return str(previous["status"])

    record_document(connection, digest, source, "PREPARING", increment_attempt=True)
    env = os.environ.copy()
    env["DATA_HERMETICA_INVOICE_ENGINE_ROOT"] = str(root)
    if "OneDriveCommercial" not in env:
        env["OneDriveCommercial"] = str(intake.parents[1])

    python = str(config.get("python_executable") or (Path(sys.executable).parent / "python.exe"))
    prepare_script = root / "app" / "invoice_prepare.py"
    worker_script = root / "app" / "invoice_worker.py"
    if not prepare_script.is_file() or not worker_script.is_file():
        raise FileNotFoundError("invoice_prepare.py or invoice_worker.py is missing from app folder")

    prepare_result = subprocess.run(
        [python, str(prepare_script), "--file", str(source)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=int(config.get("prepare_timeout_seconds", 900)),
        check=False,
        env=env,
    )
    if prepare_result.stdout.strip():
        logger.info("Preparation summary for %s: %s", source.name, prepare_result.stdout.strip().replace("\n", " | ")[:2000])
    if prepare_result.stderr.strip():
        logger.warning("Preparation diagnostic for %s: %s", source.name, prepare_result.stderr.strip().replace("\n", " | ")[:2000])
    if prepare_result.returncode != 0:
        message = f"Preparation failed with exit code {prepare_result.returncode}"
        record_document(connection, digest, source, "FAILED", error=message)
        logger.error("%s: %s", message, source.name)
        return "FAILED"

    manifest = root / "work" / "prepared" / digest / "manifest.json"
    if not manifest.is_file():
        message = f"Preparation completed without expected manifest: {manifest}"
        record_document(connection, digest, source, "FAILED", error=message)
        logger.error("%s", message)
        return "FAILED"
    record_document(connection, digest, source, "PREPARED")

    worker_result = subprocess.run(
        [python, str(worker_script), "--sha256", digest],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=int(config.get("worker_process_timeout_seconds", 2100)),
        check=False,
        env=env,
    )
    if worker_result.stdout.strip():
        logger.info("Worker summary for %s: %s", source.name, worker_result.stdout.strip().replace("\n", " | ")[:3000])
    if worker_result.stderr.strip():
        logger.warning("Worker diagnostic for %s: %s", source.name, worker_result.stderr.strip().replace("\n", " | ")[:3000])

    final_worker_status = worker_job_status(worker_db, digest)
    if worker_result.returncode == 0 and final_worker_status == "COMPLETED":
        record_document(connection, digest, source, "COMPLETED", worker_status=final_worker_status)
        logger.info("Completed invoice: %s", source.name)
        return "COMPLETED"
    if final_worker_status == "REVIEW_REQUIRED":
        message = f"Invoice worker requires review; see H:\\DataHermetica\\InvoiceEngine logs for {digest}"
        record_document(
            connection, digest, source, "REVIEW_REQUIRED",
            worker_status=final_worker_status, error=message,
        )
        logger.warning("%s: %s", message, source.name)
        return "REVIEW_REQUIRED"

    message = f"Invoice worker failed with exit code {worker_result.returncode}; worker state={final_worker_status}"
    record_document(
        connection, digest, source, "FAILED",
        worker_status=final_worker_status, error=message,
    )
    logger.error("%s: %s", message, source.name)
    return "FAILED"


def scan_once(
    intake: Path,
    *,
    root: Path,
    config: dict[str, Any],
    connection: sqlite3.Connection,
    logger: logging.Logger,
) -> int:
    if not intake.is_dir():
        raise FileNotFoundError(f"Production intake directory does not exist: {intake}")
    candidates = sorted(
        (
            path for path in intake.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        ),
        key=lambda path: (path.stat().st_mtime_ns, path.name.casefold()),
    )
    if candidates and not lm_studio_model_ready(root, config, logger):
        logger.info(
            "Folder scan deferred: %s supported input file(s) remain in Incoming.",
            len(candidates),
        )
        return 0

    processed = 0
    for source in candidates:
        try:
            source_stat = source.stat()
            if known_path_unchanged(connection, source, source_stat):
                continue
            process_one(
                source,
                root=root,
                intake=intake,
                config=config,
                connection=connection,
                logger=logger,
            )
            processed += 1
        except TimeoutError as exc:
            logger.info("Input is not ready yet; will check again: %s (%s)", source.name, exc)
        except Exception as exc:  # Record concise error; traceback stays in supervisor log only.
            logger.exception("Unexpected supervisor failure for %s: %s", source.name, exc)
    logger.info("Folder scan completed: files=%s processed_or_reviewed=%s", len(candidates), processed)
    return processed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", help="Engine root; defaults to environment or script location")
    parser.add_argument("--intake", help="Override configured OneDrive Incoming directory")
    parser.add_argument("--once", action="store_true", help="Run one folder scan and exit")
    parser.add_argument("--continuous", action="store_true", help="Poll continuously (default mode)")
    parser.add_argument("--poll-interval", type=int, help="Override folder scan interval in seconds")
    args = parser.parse_args()

    try:
        root = root_from_args(args.engine_root)
        config_path = root / "config" / "invoice_supervisor_config.json"
        config = json_file(config_path)
        intake = intake_from_config(config, args.intake)
        logger = setup_logging(root, config)
        logger.info("Supervisor starting; engine_root=%s intake=%s", root, intake)

        if not intake.is_dir():
            raise FileNotFoundError(f"Production intake directory does not exist: {intake}")
        if not (root / "app" / "invoice_prepare.py").is_file():
            raise FileNotFoundError(f"Missing {root / 'app' / 'invoice_prepare.py'}")
        if not (root / "app" / "invoice_worker.py").is_file():
            raise FileNotFoundError(f"Missing {root / 'app' / 'invoice_worker.py'}")

        lock = take_single_instance_lock(root)
        if lock is None:
            logger.info("Another supervisor instance holds the lock; exiting without work.")
            return 0
        connection = open_state_database(root / "state" / "supervisor.db")
        try:
            if args.once:
                scan_once(
                    intake, root=root, config=config,
                    connection=connection, logger=logger,
                )
                return 0

            interval = args.poll_interval or int(config.get("poll_interval_seconds", 30))
            if interval < 5:
                raise ValueError("poll interval must be at least 5 seconds")
            while True:
                scan_once(
                    intake, root=root, config=config,
                    connection=connection, logger=logger,
                )
                time.sleep(interval)
        finally:
            connection.close()
            release_single_instance_lock(lock)
            logger.info("Supervisor stopped.")
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
