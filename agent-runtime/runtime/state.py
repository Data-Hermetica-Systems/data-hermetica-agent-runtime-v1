from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


AgentRunStatus = Literal[
    "initialized",
    "running",
    "completed",
    "completed_with_exceptions",
    "failed",
]


class AgentAuditEvent(BaseModel):
    event_type: str
    message: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    details: dict[str, Any] = Field(default_factory=dict)


class AgentRuntimeState(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    runtime_name: str = "Data Hermetica Agent Runtime"
    runtime_version: str = "v1"
    status: AgentRunStatus = "initialized"

    project_root: str | None = None
    current_stage: str = "startup"

    input_pdf_paths: list[str] = Field(default_factory=list)
    completed_stages: list[str] = Field(default_factory=list)
    failed_stages: list[str] = Field(default_factory=list)

    script_results: list[dict[str, Any]] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    missing_outputs: list[str] = Field(default_factory=list)

    metrics: dict[str, Any] = Field(default_factory=dict)
    validation_flags: list[dict[str, Any]] = Field(default_factory=list)

    has_validation_errors: bool = False
    all_row_counts_matched: bool | None = None
    all_validation_clear: bool | None = None
    human_review_required: bool = False

    exception_summary: str | None = None
    repair_recommendations: list[str] = Field(default_factory=list)
    final_outputs: dict[str, str] = Field(default_factory=dict)

    audit_events: list[AgentAuditEvent] = Field(default_factory=list)

    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    finished_at: str | None = None

    def add_audit_event(
        self,
        event_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.audit_events.append(
            AgentAuditEvent(
                event_type=event_type,
                message=message,
                details=details or {},
            )
        )

    def mark_completed_stage(self, stage_name: str) -> None:
        if stage_name not in self.completed_stages:
            self.completed_stages.append(stage_name)
        self.current_stage = stage_name
        self.add_audit_event(
            event_type="stage_completed",
            message=f"Completed stage: {stage_name}",
        )

    def mark_failed_stage(self, stage_name: str, error_message: str) -> None:
        if stage_name not in self.failed_stages:
            self.failed_stages.append(stage_name)
        self.status = "failed"
        self.current_stage = stage_name
        self.add_audit_event(
            event_type="stage_failed",
            message=f"Failed stage: {stage_name}",
            details={"error_message": error_message},
        )

    def finish(self, status: AgentRunStatus) -> None:
        self.status = status
        self.finished_at = datetime.now(timezone.utc).isoformat()
        self.add_audit_event(
            event_type="run_finished",
            message=f"Agent runtime finished with status: {status}",
        )
