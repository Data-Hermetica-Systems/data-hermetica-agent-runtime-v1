from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ExpectedOutputCheck(BaseModel):
    path: str
    exists: bool
    size_bytes: int | None = None


class NodeScriptResult(BaseModel):
    script_name: str
    script_path: str
    status: str
    exit_code: int | None
    duration_ms: int
    expected_outputs: list[ExpectedOutputCheck] = Field(default_factory=list)
    missing_outputs: list[str] = Field(default_factory=list)
    stdout_tail: str = ""
    stderr_tail: str = ""
    error_message: str | None = None


def _tail_text(value: str, max_chars: int = 4000) -> str:
    if not value:
        return ""
    return value[-max_chars:]


def _check_expected_outputs(
    project_root: Path,
    expected_outputs: list[str] | None,
) -> tuple[list[ExpectedOutputCheck], list[str]]:
    checks: list[ExpectedOutputCheck] = []
    missing: list[str] = []

    for relative_path in expected_outputs or []:
        output_path = project_root / relative_path
        exists = output_path.exists()
        size_bytes = output_path.stat().st_size if exists and output_path.is_file() else None

        checks.append(
            ExpectedOutputCheck(
                path=relative_path,
                exists=exists,
                size_bytes=size_bytes,
            )
        )

        if not exists:
            missing.append(relative_path)

    return checks, missing


def run_node_script(
    project_root: str | Path,
    script_relative_path: str,
    expected_outputs: list[str] | None = None,
    timeout_seconds: int = 120,
) -> NodeScriptResult:
    root = Path(project_root).resolve()
    script_path = root / script_relative_path

    started = time.perf_counter()

    if not script_path.exists():
        duration_ms = int((time.perf_counter() - started) * 1000)
        return NodeScriptResult(
            script_name=Path(script_relative_path).name,
            script_path=str(script_path),
            status="failed",
            exit_code=None,
            duration_ms=duration_ms,
            error_message=f"Node script not found: {script_path}",
        )

    try:
        completed = subprocess.run(
            ["node", str(script_path)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )

        duration_ms = int((time.perf_counter() - started) * 1000)
        output_checks, missing_outputs = _check_expected_outputs(root, expected_outputs)

        status = "completed" if completed.returncode == 0 and not missing_outputs else "failed"

        error_message = None
        if completed.returncode != 0:
            error_message = f"Node script exited with code {completed.returncode}"
        elif missing_outputs:
            error_message = "Node script completed but expected outputs are missing."

        return NodeScriptResult(
            script_name=Path(script_relative_path).name,
            script_path=str(script_path),
            status=status,
            exit_code=completed.returncode,
            duration_ms=duration_ms,
            expected_outputs=output_checks,
            missing_outputs=missing_outputs,
            stdout_tail=_tail_text(completed.stdout),
            stderr_tail=_tail_text(completed.stderr),
            error_message=error_message,
        )

    except subprocess.TimeoutExpired as error:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return NodeScriptResult(
            script_name=Path(script_relative_path).name,
            script_path=str(script_path),
            status="failed",
            exit_code=None,
            duration_ms=duration_ms,
            stdout_tail=_tail_text(error.stdout or ""),
            stderr_tail=_tail_text(error.stderr or ""),
            error_message=f"Node script timed out after {timeout_seconds} seconds.",
        )

    except Exception as error:
        duration_ms = int((time.perf_counter() - started) * 1000)
        return NodeScriptResult(
            script_name=Path(script_relative_path).name,
            script_path=str(script_path),
            status="failed",
            exit_code=None,
            duration_ms=duration_ms,
            error_message=str(error),
        )


def result_to_dict(result: NodeScriptResult) -> dict[str, Any]:
    return result.model_dump()
