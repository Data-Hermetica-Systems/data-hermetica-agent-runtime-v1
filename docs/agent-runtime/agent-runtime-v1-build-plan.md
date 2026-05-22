# Data Hermetica Agent Runtime v1 — Codex Build Plan

**Purpose:** Convert the existing private document intelligence pipeline into a local-first, graph-orchestrated agentic runtime for logistics/customs document operations.

**Target repo:** `Data-Hermetica-Systems/private-document-intelligence-pipeline`

**Target local path:** `H:\DataHermetica\local-ai-document-core`

**Build window:** 1 week

**Primary implementation mode:** Codex / AI coding agent following this markdown file as the canonical instruction source.

---

## 0. Non-Negotiable Mission

Build **Data Hermetica Agent Runtime v1** inside the existing repo.

The current repo is already a working deterministic document intelligence pipeline. Do not replace it. Convert it into the **tool execution layer** of an agentic runtime.

The target system is:

```text
Deterministic document intelligence core
+
LangGraph-style agentic control plane
+
validation-driven routing
+
exception handling
+
audit logging
+
evaluation harness
```

The runtime must be local-first, private-first, and suitable for future integration with Power Platform, Dataverse, Power Automate, and Power Apps.

---

## 1. Existing Repo Context

The repo currently processes logistics/customs/commercial invoice PDFs into validated canonical JSON and CSV outputs.

Current deterministic pipeline:

```text
PDF invoices
→ Poppler page rendering
→ Tesseract OCR
→ OCR text output
→ invoice-family recognition
→ item segmentation
→ header metadata extraction
→ deterministic canonical row building
→ special-family parsing
→ field normalization
→ validation
→ weight-total reconciliation
→ individual JSON output
→ individual CSV output
→ master JSON output
→ master CSV output
→ master validation flags CSV
→ master pipeline summary
```

Existing main runner:

```text
src/run-private-document-pipeline.js
```

Existing runner steps:

```text
STEP 1: OCR PDF invoices with Tesseract
STEP 2: Segment OCR invoice items
STEP 3: Build deterministic canonical rows from segmented Honeywell invoices
STEP 4: Build canonical rows for special invoice families
STEP 5: Reconcile invoice weight totals
STEP 6: Build master canonical JSON and CSV output
```

Existing scripts:

```text
src/ocr-pdf-with-tesseract.js
src/segment-ocr-invoice-items.js
src/build-canonical-rows-from-segments.js
src/build-canonical-rows-for-special-families.js
src/reconcile-invoice-weight-totals.js
src/build-master-canonical-output.js
src/run-private-document-pipeline.js
```

Existing key outputs:

```text
outputs/master-canonical-invoice-lines.json
outputs/master-canonical-invoice-lines.csv
outputs/master-validation-flags.csv
outputs/master-pipeline-run-summary.json
outputs/weight-reconciliation-summary.json
```

Existing canonical schema:

```text
SourceInvoiceFile
SourceParser
InvoiceNumber
InvoiceDate
ShipmentNumber
InvoiceFamily
LineNo
ProductNumber
Description
Unit
Quantity
UnitPriceUSD
LineAmountUSD
CommodityCode
CountryOfOrigin
DeliveryNote
OrderNumber
NetWeightKG
GrossWeightKG
```

Existing current/future architecture already points toward:

```text
PaddleOCR PP-StructureV3
BGE-M3 embeddings
Qdrant
local/private LLM fallback
Qwen models
Dataverse
Power Automate approval flow
Power Apps exception review
ERP/customs/finance integration
```

But v1 should not implement everything. v1 must implement the local agentic runtime foundation.

---

## 2. What Agent Runtime v1 Means

Agent Runtime v1 is not a chatbot.

Agent Runtime v1 is a local graph-orchestrated execution engine that:

```text
receives a document-processing job
→ creates persistent run state
→ executes deterministic pipeline tools
→ records tool outputs
→ inspects validation results
→ routes clean jobs vs exception jobs
→ retries safe failures when appropriate
→ generates human-review artifacts
→ writes audit logs
→ produces final structured outputs
```

The first true agentic behavior is **validation-driven routing**:

```text
IF pipeline outputs are valid and clean
  → mark run as completed_clean
  → write final audit log
ELSE
  → mark run as completed_with_exceptions
  → summarize validation problems
  → generate human-review queue
  → generate repair recommendations
  → write final audit log
```

---

## 3. High-Level Architecture

Target v1 architecture:

```text
START
  ↓
intake_node
  ↓
run_ocr_node
  ↓
segment_items_node
  ↓
build_canonical_rows_node
  ↓
run_special_family_parser_node
  ↓
reconcile_weights_node
  ↓
build_master_output_node
  ↓
inspect_validation_node
  ↓
validation_router
  ├── clean_finish → audit_node → END
  └── exception_route → repair_recommendation_node → exception_router_node → audit_node → END
```

Implementation principle:

```text
Existing Node.js scripts = tools
Python/LangGraph runtime = orchestration/control plane
Validation summaries = routing source of truth
Audit logs = persistent state and explainability layer
```

---

## 4. Technology Stack for v1

Use the following stack unless there is a concrete blocker:

| Layer | Technology | Purpose |
|---|---|---|
| Agent orchestration | LangGraph Python | Stateful graph execution |
| Runtime language | Python | Agent control plane |
| Existing pipeline | Node.js CommonJS | Deterministic document tools |
| Tool execution bridge | Python subprocess | Run existing Node scripts safely |
| Validation schema | Pydantic | Runtime state and output contracts |
| Config | python-dotenv | Local configuration |
| Output display | rich | readable CLI output |
| Runtime storage | JSON files first | simple persistent audit/run state |
| Future state storage | SQLite | optional after v1 |
| Future RAG | Qdrant + BGE-M3 | vendor/context rule retrieval later |
| Future API | FastAPI | Power Automate custom connector bridge later |

Do not make LLM calls central in v1.

LLM usage, if added, should be limited to:

```text
exception summary
repair recommendation
human-readable audit explanation
```

Deterministic logic must remain responsible for:

```text
OCR execution
segmentation
canonical row building
number parsing
weight reconciliation
required-field validation
row-count validation
JSON/CSV output
```

---

## 5. Required Folder Structure to Add

Create this structure inside the repo:

```text
agent-runtime/
  README.md
  requirements.txt
  .env.example

  runtime/
    __init__.py
    state.py
    graph.py
    config.py
    run_agentic_document_job.py

  runtime/nodes/
    __init__.py
    intake_node.py
    run_ocr_node.py
    segment_items_node.py
    build_canonical_rows_node.py
    run_special_family_parser_node.py
    reconcile_weights_node.py
    build_master_output_node.py
    inspect_validation_node.py
    exception_router_node.py
    repair_recommendation_node.py
    audit_node.py

  runtime/tools/
    __init__.py
    node_script_tool.py
    file_system_tool.py
    output_reader_tool.py
    validation_summary_tool.py

  runtime/schemas/
    __init__.py
    document_job.py
    pipeline_state.py
    validation_issue.py
    agent_decision.py

  runtime/prompts/
    classify_document.md
    repair_recommendation.md
    exception_summary.md

  runtime/evals/
    expected_clean_run.json
    expected_exception_run.json
    eval_agent_runtime.py

  runtime/storage/
    .gitkeep
```

Also add these root-level docs:

```text
docs/agent-runtime-architecture.md
docs/agent-state-schema.md
docs/agent-node-contracts.md
docs/agent-runtime-week1-plan.md
docs/agent-runtime-demo-script.md
docs/agent-runtime-business-case.md
```

---

## 6. Required Package Script Updates

Update root `package.json`.

Current default test command should be replaced. Use this full target shape:

```json
{
  "name": "local-ai-document-core",
  "version": "1.0.0",
  "description": "Local-first private document intelligence and agentic runtime for logistics and customs document processing.",
  "main": "index.js",
  "directories": {
    "doc": "docs",
    "test": "tests"
  },
  "scripts": {
    "pipeline:run": "node src/run-private-document-pipeline.js",
    "agent:run": "cd agent-runtime && .venv\\Scripts\\python.exe runtime\\run_agentic_document_job.py",
    "agent:eval": "cd agent-runtime && .venv\\Scripts\\python.exe runtime\\evals\\eval_agent_runtime.py"
  },
  "keywords": [
    "document-intelligence",
    "agentic-ai",
    "logistics",
    "customs",
    "ocr",
    "validation",
    "langgraph",
    "power-platform"
  ],
  "author": "Data Hermetica Systems",
  "license": "UNLICENSED",
  "type": "commonjs"
}
```

If the repo has additional fields not shown here, preserve them unless they conflict.

---

## 7. Virtual Environment Setup

Expected Windows setup commands:

```powershell
cd H:\DataHermetica\local-ai-document-core
mkdir agent-runtime
cd agent-runtime
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install langgraph langchain langchain-community pydantic python-dotenv rich
pip freeze > requirements.txt
```

The generated `requirements.txt` should include the installed libraries and their versions.

---

## 8. Runtime State Schema

Create `agent-runtime/runtime/state.py` and/or `agent-runtime/runtime/schemas/pipeline_state.py`.

The state must include at least:

```text
run_id
job_name
project_root
started_at
finished_at
status
current_stage
completed_stages
failed_stages
script_results
expected_outputs
missing_outputs
metrics
validation_flags
has_validation_errors
all_row_counts_matched
all_validation_clear
human_review_required
exception_summary
repair_recommendations
final_outputs
audit_events
error_message
```

Recommended Pydantic model fields:

```python
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class ScriptResult(BaseModel):
    script_name: str
    status: Literal["completed", "failed", "skipped"]
    exit_code: int | None = None
    started_at: str | None = None
    finished_at: str | None = None
    duration_ms: int | None = None
    expected_outputs: list[dict[str, Any]] = Field(default_factory=list)
    missing_outputs: list[str] = Field(default_factory=list)
    stdout_tail: str | None = None
    stderr_tail: str | None = None
    error_message: str | None = None


class AuditEvent(BaseModel):
    event_type: str
    stage: str
    message: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    detail: dict[str, Any] = Field(default_factory=dict)


class AgentRuntimeState(BaseModel):
    run_id: str
    job_name: str = "default_document_pipeline_job"
    project_root: str
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    finished_at: str | None = None
    status: str = "initialized"
    current_stage: str = "initialized"
    completed_stages: list[str] = Field(default_factory=list)
    failed_stages: list[str] = Field(default_factory=list)
    script_results: list[ScriptResult] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    missing_outputs: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    validation_flags: list[dict[str, Any]] = Field(default_factory=list)
    has_validation_errors: bool = False
    all_row_counts_matched: bool = False
    all_validation_clear: bool = False
    human_review_required: bool = False
    exception_summary: str | None = None
    repair_recommendations: list[str] = Field(default_factory=list)
    final_outputs: dict[str, str] = Field(default_factory=dict)
    audit_events: list[AuditEvent] = Field(default_factory=list)
    error_message: str | None = None
```

Codex may adjust imports or paths, but preserve the schema intent.

---

## 9. Node Script Tool Contract

Create:

```text
agent-runtime/runtime/tools/node_script_tool.py
```

This tool must:

1. Accept `project_root`, `script_relative_path`, `expected_outputs`.
2. Run the Node script using `subprocess.run`.
3. Capture stdout and stderr.
4. Record start time, finish time, and duration.
5. Check expected output files.
6. Return a `ScriptResult`-compatible object/dict.
7. Never silently ignore errors.
8. Never delete user data.

Tool behavior:

```text
If script exits with code 0 and expected files exist:
  status = completed

If script exits nonzero:
  status = failed
  include stderr_tail and error_message

If script exits zero but expected files are missing:
  status = failed
  include missing_outputs
```

Suggested implementation pattern:

```python
from __future__ import annotations

import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def tail_text(value: str, max_chars: int = 4000) -> str:
    if not value:
        return ""
    return value[-max_chars:]


def run_node_script(
    project_root: str,
    script_relative_path: str,
    expected_outputs: list[str] | None = None,
) -> dict[str, Any]:
    expected_outputs = expected_outputs or []
    root = Path(project_root).resolve()
    script_path = root / script_relative_path

    started_at = utc_now()
    started_ms = time.time_ns() // 1_000_000

    if not script_path.exists():
        return {
            "script_name": script_relative_path,
            "status": "failed",
            "exit_code": None,
            "started_at": started_at,
            "finished_at": utc_now(),
            "duration_ms": 0,
            "expected_outputs": [],
            "missing_outputs": [],
            "stdout_tail": "",
            "stderr_tail": "",
            "error_message": f"Script not found: {script_path}",
        }

    result = subprocess.run(
        ["node", str(script_path)],
        cwd=str(root),
        capture_output=True,
        text=True,
        shell=False,
    )

    finished_at = utc_now()
    finished_ms = time.time_ns() // 1_000_000

    output_checks = []
    missing_outputs = []

    for output in expected_outputs:
        full_output_path = root / output
        exists = full_output_path.exists()
        output_checks.append({
            "path": output,
            "exists": exists,
            "size_bytes": full_output_path.stat().st_size if exists else None,
        })
        if not exists:
            missing_outputs.append(output)

    status = "completed"
    error_message = None

    if result.returncode != 0:
        status = "failed"
        error_message = f"Node script exited with code {result.returncode}: {script_relative_path}"
    elif missing_outputs:
        status = "failed"
        error_message = f"Node script completed but expected outputs are missing: {', '.join(missing_outputs)}"

    return {
        "script_name": script_relative_path,
        "status": status,
        "exit_code": result.returncode,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": finished_ms - started_ms,
        "expected_outputs": output_checks,
        "missing_outputs": missing_outputs,
        "stdout_tail": tail_text(result.stdout),
        "stderr_tail": tail_text(result.stderr),
        "error_message": error_message,
    }
```

---

## 10. Expected Output Map for Each Existing Script

Use this expected output map in graph nodes.

### OCR node

Script:

```text
src/ocr-pdf-with-tesseract.js
```

Expected outputs:

```text
ocr/tesseract-ocr-run-summary.json
ocr/sample-commercial-invoice-001-tesseract-ocr.txt
ocr/sample-commercial-invoice-002-tesseract-ocr.txt
ocr/sample-commercial-invoice-003-tesseract-ocr.txt
ocr/sample-commercial-invoice-004-tesseract-ocr.txt
ocr/sample-commercial-invoice-005-tesseract-ocr.txt
```

### Segmentation node

Script:

```text
src/segment-ocr-invoice-items.js
```

Expected outputs:

```text
ocr/segmented-items-summary.json
ocr/sample-commercial-invoice-001-segmented-items.json
ocr/sample-commercial-invoice-002-segmented-items.json
ocr/sample-commercial-invoice-003-segmented-items.json
ocr/sample-commercial-invoice-004-segmented-items.json
ocr/sample-commercial-invoice-005-segmented-items.json
```

### Deterministic canonical row node

Script:

```text
src/build-canonical-rows-from-segments.js
```

Expected outputs:

```text
outputs/deterministic-canonical-lines-summary.json
outputs/sample-commercial-invoice-001-deterministic-canonical-lines.json
outputs/sample-commercial-invoice-001-deterministic-canonical-lines.csv
outputs/sample-commercial-invoice-002-deterministic-canonical-lines.json
outputs/sample-commercial-invoice-002-deterministic-canonical-lines.csv
outputs/sample-commercial-invoice-003-deterministic-canonical-lines.json
outputs/sample-commercial-invoice-003-deterministic-canonical-lines.csv
```

### Special-family parser node

Script:

```text
src/build-canonical-rows-for-special-families.js
```

Expected outputs:

```text
outputs/special-family-canonical-lines-summary.json
outputs/sample-commercial-invoice-004-special-family-canonical-lines.json
outputs/sample-commercial-invoice-004-special-family-canonical-lines.csv
outputs/sample-commercial-invoice-005-special-family-canonical-lines.json
outputs/sample-commercial-invoice-005-special-family-canonical-lines.csv
```

### Weight reconciliation node

Script:

```text
src/reconcile-invoice-weight-totals.js
```

Expected outputs:

```text
outputs/weight-reconciliation-summary.json
outputs/sample-commercial-invoice-001-weight-reconciliation.json
outputs/sample-commercial-invoice-002-weight-reconciliation.json
outputs/sample-commercial-invoice-003-weight-reconciliation.json
```

### Master output node

Script:

```text
src/build-master-canonical-output.js
```

Expected outputs:

```text
outputs/master-canonical-invoice-lines.json
outputs/master-canonical-invoice-lines.csv
outputs/master-validation-flags.csv
```

---

## 11. Node Implementation Rules

Each graph node must:

1. Accept the runtime state.
2. Add an audit event at start.
3. Execute exactly one responsibility.
4. Update `current_stage`.
5. Append completed or failed stage name.
6. Append script result when a tool is executed.
7. Set `status = failed` and `error_message` if failure occurs.
8. Return updated state.

Required node names:

```text
intake_node
run_ocr_node
segment_items_node
build_canonical_rows_node
run_special_family_parser_node
reconcile_weights_node
build_master_output_node
inspect_validation_node
repair_recommendation_node
exception_router_node
audit_node
```

---

## 12. Validation Inspection Logic

Create:

```text
agent-runtime/runtime/tools/validation_summary_tool.py
agent-runtime/runtime/nodes/inspect_validation_node.py
```

This must read:

```text
outputs/master-pipeline-run-summary.json
outputs/master-canonical-invoice-lines.json
outputs/master-validation-flags.csv
outputs/weight-reconciliation-summary.json
```

Primary source should be:

```text
outputs/master-pipeline-run-summary.json
```

Extract at least:

```text
metrics.totalExpectedRows
metrics.totalRowsExtracted
metrics.sourceValidationFlagCount
metrics.masterValidationFlagCount
metrics.totalValidationFlagCount
metrics.hasValidationErrors
metrics.allRowCountsMatched
metrics.allValidationClear
metrics.lineAmountGrandTotalUSD
metrics.netWeightGrandTotalKG
metrics.grossWeightGrandTotalKG
metrics.masterValidationFlagsCsvCreated
metrics.weightReconciliationSummaryCreated
```

Set state:

```text
state.metrics = extracted metrics
state.has_validation_errors = metrics.hasValidationErrors
state.all_row_counts_matched = metrics.allRowCountsMatched
state.all_validation_clear = metrics.allValidationClear
state.human_review_required = NOT metrics.allValidationClear OR metrics.hasValidationErrors OR totalValidationFlagCount > 0
```

Routing rule:

```text
If all_validation_clear is true AND has_validation_errors is false AND totalValidationFlagCount is 0:
  route to clean_finish / audit_node
Else:
  route to exception path
```

---

## 13. Exception Routing Logic

Create:

```text
agent-runtime/runtime/nodes/repair_recommendation_node.py
agent-runtime/runtime/nodes/exception_router_node.py
```

The exception path must generate these files:

```text
outputs/agent-exception-summary.json
outputs/agent-human-review-queue.csv
outputs/agent-repair-recommendations.md
```

### Exception conditions

| Condition | Required decision |
|---|---|
| Missing output file | Pipeline failure; human review required |
| Node script nonzero exit | Pipeline failure; human review required |
| Row count mismatch | Human review required |
| Weight reconciliation mismatch | Human review required |
| Total validation flags > 0 | Human review required |
| All validation clear | No human review required |
| Segmented item count = 0 for known special-family invoice | Do not treat as error by itself |

### Human review queue CSV columns

```text
RunId
IssueType
Severity
Source
InvoiceNumber
ShipmentNumber
FieldName
ObservedValue
ExpectedValue
Recommendation
RequiresHumanReview
```

If exact values are not available, use `N/A`. Do not invent values.

### Repair recommendation style

`outputs/agent-repair-recommendations.md` should be deterministic and business-readable.

Example:

```markdown
# Agent Repair Recommendations

## Run

- Run ID: ...
- Status: completed_with_exceptions
- Human review required: true

## Summary

The deterministic pipeline completed, but validation flags require human review before downstream writeback.

## Recommended Review Actions

1. Review weight reconciliation mismatches.
2. Compare line-level net/gross weights against invoice bottom totals.
3. Confirm whether European decimal interpretation should be applied.
4. Do not write affected records to Dataverse until reviewed.
```

---

## 14. Audit Log Requirements

Create:

```text
agent-runtime/runtime/nodes/audit_node.py
```

The audit node must write:

```text
agent-runtime/runtime/storage/{run_id}.json
outputs/agent-runtime-run-summary.json
```

Audit output must include:

```text
run_id
job_name
started_at
finished_at
status
current_stage
completed_stages
failed_stages
script_results
metrics
has_validation_errors
all_row_counts_matched
all_validation_clear
human_review_required
exception_summary
repair_recommendations
final_outputs
audit_events
error_message
```

Status values:

```text
initialized
running
completed_clean
completed_with_exceptions
failed
```

---

## 15. LangGraph Graph Requirements

Create:

```text
agent-runtime/runtime/graph.py
```

Use LangGraph to define the graph.

The graph must support conditional routing after validation inspection.

Pseudo-structure:

```python
from langgraph.graph import StateGraph, END


def route_after_validation(state):
    if state.get("status") == "failed":
        return "audit"
    if state.get("human_review_required"):
        return "repair_recommendation"
    return "audit"


def build_graph():
    graph = StateGraph(dict)

    graph.add_node("intake", intake_node)
    graph.add_node("run_ocr", run_ocr_node)
    graph.add_node("segment_items", segment_items_node)
    graph.add_node("build_canonical_rows", build_canonical_rows_node)
    graph.add_node("run_special_family_parser", run_special_family_parser_node)
    graph.add_node("reconcile_weights", reconcile_weights_node)
    graph.add_node("build_master_output", build_master_output_node)
    graph.add_node("inspect_validation", inspect_validation_node)
    graph.add_node("repair_recommendation", repair_recommendation_node)
    graph.add_node("exception_router", exception_router_node)
    graph.add_node("audit", audit_node)

    graph.set_entry_point("intake")

    graph.add_edge("intake", "run_ocr")
    graph.add_edge("run_ocr", "segment_items")
    graph.add_edge("segment_items", "build_canonical_rows")
    graph.add_edge("build_canonical_rows", "run_special_family_parser")
    graph.add_edge("run_special_family_parser", "reconcile_weights")
    graph.add_edge("reconcile_weights", "build_master_output")
    graph.add_edge("build_master_output", "inspect_validation")

    graph.add_conditional_edges(
        "inspect_validation",
        route_after_validation,
        {
            "repair_recommendation": "repair_recommendation",
            "audit": "audit",
        },
    )

    graph.add_edge("repair_recommendation", "exception_router")
    graph.add_edge("exception_router", "audit")
    graph.add_edge("audit", END)

    return graph.compile()
```

If using typed Pydantic state with LangGraph creates friction, use dict state in v1 and validate at boundaries.

---

## 16. CLI Runner Requirements

Create:

```text
agent-runtime/runtime/run_agentic_document_job.py
```

It must:

1. Resolve repo root.
2. Generate a run ID.
3. Create initial state.
4. Invoke the compiled graph.
5. Print final summary to console.
6. Exit with code 0 for `completed_clean` or `completed_with_exceptions`.
7. Exit with code 1 for `failed`.

Run command:

```powershell
npm run agent:run
```

Expected successful console output shape:

```text
============================================================
Data Hermetica Agent Runtime v1
============================================================
Run ID: 2026-05-21T...
Status: completed_with_exceptions
Human review required: true
OCR: completed
Segmentation: completed
Canonical extraction: completed
Special-family parsing: completed
Weight reconciliation: completed
Master output: completed
Validation inspection: completed
Audit log: created
Agent summary: outputs/agent-runtime-run-summary.json
============================================================
```

---

## 17. Evaluation Harness Requirements

Create:

```text
agent-runtime/runtime/evals/eval_agent_runtime.py
```

Run command:

```powershell
npm run agent:eval
```

Evaluation checks:

| Eval | Pass condition |
|---|---|
| Agent runner starts | process completes |
| Pipeline runs | all script stages complete or known exception path is handled |
| Master output exists | `outputs/master-canonical-invoice-lines.json` exists |
| Master CSV exists | `outputs/master-canonical-invoice-lines.csv` exists |
| Validation CSV exists | `outputs/master-validation-flags.csv` exists |
| Agent audit exists | `outputs/agent-runtime-run-summary.json` exists |
| Runtime state saved | `agent-runtime/runtime/storage/{run_id}.json` exists |
| Metrics parsed | row counts and validation fields available |
| Routing correct | human_review_required matches validation status |
| No silent failure | failed scripts produce failed status and error message |

The eval script should print a table-like summary and exit nonzero if any required check fails.

Example output:

```text
Data Hermetica Agent Runtime Eval

[PASS] agent runtime summary exists
[PASS] master canonical JSON exists
[PASS] master canonical CSV exists
[PASS] validation flags CSV exists
[PASS] row metrics parsed
[PASS] exception routing matches validation metrics
[PASS] audit state saved

Result: PASS
```

---

## 18. Documentation Requirements

Update or create these docs.

### `agent-runtime/README.md`

Must include:

```text
What the runtime is
How it relates to the deterministic pipeline
How to install dependencies
How to run agent runtime
How to run evals
What outputs are generated
What v1 does not do yet
```

### `docs/agent-runtime-architecture.md`

Must include:

```text
Deterministic core + agentic control plane model
Graph diagram
Node descriptions
State schema summary
Routing logic
Audit/output files
Future Power Platform integration path
```

### `docs/agent-node-contracts.md`

Must include a table:

```text
Node name
Input state fields
Tool/script called
Expected outputs
Failure conditions
State updates
Next node
```

### `docs/agent-state-schema.md`

Must describe every important state field.

### `docs/agent-runtime-demo-script.md`

Must include:

```text
30-second explanation
2-minute explanation
technical walkthrough
interview answer
```

### `docs/agent-runtime-business-case.md`

Must explain business value:

```text
manual logistics/customs document work
private local processing
validated structured outputs
exception routing
auditability
future Dataverse/Power Automate integration
```

---

## 19. README Update Requirement

Add a new section to root `README.md`:

```markdown
## Data Hermetica Agent Runtime v1

This repo now includes an experimental local agentic runtime layer built around the deterministic document intelligence pipeline.

The agent runtime does not replace deterministic validation. It orchestrates the existing document-processing tools, records persistent run state, inspects validation metrics, routes clean vs exception paths, generates human-review artifacts, and writes audit logs.

### Runtime Flow

```text
Document job
→ agent runtime state
→ OCR tool node
→ segmentation tool node
→ canonical extraction tool nodes
→ weight reconciliation tool node
→ master output tool node
→ validation inspection
→ clean finish or exception route
→ audit log
```

### Commands

```powershell
npm run pipeline:run
npm run agent:run
npm run agent:eval
```

### v1 Outputs

```text
outputs/agent-runtime-run-summary.json
outputs/agent-exception-summary.json
outputs/agent-human-review-queue.csv
outputs/agent-repair-recommendations.md
agent-runtime/runtime/storage/{run_id}.json
```
```

---

## 20. Implementation Phases and Commits

Use small commits.

### Commit 1: Add agent runtime scaffold

Files:

```text
agent-runtime/README.md
agent-runtime/requirements.txt
agent-runtime/.env.example
agent-runtime/runtime/__init__.py
agent-runtime/runtime/config.py
agent-runtime/runtime/state.py
agent-runtime/runtime/storage/.gitkeep
```

### Commit 2: Add Python wrapper for Node scripts

Files:

```text
agent-runtime/runtime/tools/node_script_tool.py
agent-runtime/runtime/tools/file_system_tool.py
agent-runtime/runtime/tools/output_reader_tool.py
```

### Commit 3: Add LangGraph state and minimal graph

Files:

```text
agent-runtime/runtime/graph.py
agent-runtime/runtime/run_agentic_document_job.py
```

### Commit 4: Add pipeline summary inspection and routing

Files:

```text
agent-runtime/runtime/tools/validation_summary_tool.py
agent-runtime/runtime/nodes/inspect_validation_node.py
```

### Commit 5: Split pipeline into graph nodes

Files:

```text
agent-runtime/runtime/nodes/run_ocr_node.py
agent-runtime/runtime/nodes/segment_items_node.py
agent-runtime/runtime/nodes/build_canonical_rows_node.py
agent-runtime/runtime/nodes/run_special_family_parser_node.py
agent-runtime/runtime/nodes/reconcile_weights_node.py
agent-runtime/runtime/nodes/build_master_output_node.py
```

### Commit 6: Add exception routing and audit logs

Files:

```text
agent-runtime/runtime/nodes/repair_recommendation_node.py
agent-runtime/runtime/nodes/exception_router_node.py
agent-runtime/runtime/nodes/audit_node.py
agent-runtime/runtime/prompts/repair_recommendation.md
agent-runtime/runtime/prompts/exception_summary.md
```

### Commit 7: Add evaluation harness

Files:

```text
agent-runtime/runtime/evals/eval_agent_runtime.py
agent-runtime/runtime/evals/expected_clean_run.json
agent-runtime/runtime/evals/expected_exception_run.json
```

### Commit 8: Update README and architecture docs

Files:

```text
README.md
docs/agent-runtime-architecture.md
docs/agent-node-contracts.md
docs/agent-state-schema.md
docs/agent-runtime-week1-plan.md
docs/agent-runtime-demo-script.md
docs/agent-runtime-business-case.md
package.json
```

---

## 21. Acceptance Criteria

The build is accepted when all are true:

```text
npm run pipeline:run works
npm run agent:run works
npm run agent:eval works
agent runtime creates outputs/agent-runtime-run-summary.json
agent runtime saves state in agent-runtime/runtime/storage/{run_id}.json
agent runtime reads outputs/master-pipeline-run-summary.json
agent runtime correctly sets human_review_required
agent runtime generates exception outputs when validation is not clear
agent runtime does not overwrite deterministic business values using LLM output
agent runtime documentation explains deterministic core + agentic control plane
README has commands and runtime explanation
```

---

## 22. Things Not to Implement in v1

Do not implement these unless all v1 requirements are already complete:

```text
Do not build full chat UI.
Do not build full autonomous multi-agent system.
Do not fine-tune models.
Do not add cloud deployment.
Do not add Kubernetes.
Do not add Docker unless needed for dependency stability.
Do not add Dataverse writeback yet.
Do not add Power Apps UI yet.
Do not add Power Automate connector yet.
Do not build complex RAG yet.
Do not rewrite the Node pipeline in Python.
Do not let LLMs overwrite canonical extracted fields.
```

---

## 23. Future v2 Roadmap

After v1 is stable, build v2 features in this order:

```text
1. FastAPI wrapper around agent runtime
2. OpenAPI spec for Power Automate custom connector
3. Dataverse schema docs and mock payloads
4. Power Automate approval flow design
5. Power Apps exception review mockup
6. Qdrant + BGE-M3 vendor rule retrieval
7. Local LLM exception summarizer
8. PaddleOCR PP-StructureV3 layout/table extraction
9. Qwen2.5-VL or similar multimodal fallback for visual/layout ambiguity
10. SQLite/Postgres persistent run database
11. MCP tool interface
12. Docker packaging
13. Local GPU inference benchmark
14. Client demo pack
```

---

## 24. Business Positioning

Use this positioning in docs and demo scripts:

```text
Data Hermetica Agent Runtime is a local-first agentic operations layer for document-heavy logistics and customs workflows.

It does not blindly trust AI extraction. It combines deterministic OCR/extraction/validation tools with graph-based agentic orchestration, exception routing, audit logging, and human review.

The goal is to convert messy PDFs and OCR text into validated structured records that can later flow into Dataverse, Power Apps review screens, Power Automate approvals, ERP systems, customs workflows, and finance operations.
```

Short pitch:

```text
I converted a deterministic private document intelligence pipeline into a local agentic runtime. The runtime uses graph-based orchestration, persistent state, tool execution, validation-driven routing, exception handling, and audit logging. It keeps deterministic validation as the source of business truth and uses agentic logic for orchestration and exception resolution.
```

---

## 25. Codex Operating Rules

When Codex implements this plan:

1. Read this entire file first.
2. Inspect the existing repo before editing.
3. Preserve existing working Node scripts.
4. Prefer additive changes over destructive rewrites.
5. Do not modify private/generated folders except output files produced by runtime execution.
6. Keep deterministic business logic deterministic.
7. Add clear comments where runtime control plane calls deterministic tools.
8. Use explicit file paths.
9. Use Windows-compatible commands and paths.
10. Run checks after each major change.
11. If a design ambiguity appears, choose the simplest local-first implementation.
12. Do not introduce unnecessary cloud dependencies.
13. Keep the code understandable enough for a learner to explain and modify.
14. Update docs as implementation changes.
15. Keep every node small and single-purpose.

---

## 26. First Prompt to Give Codex

Use this prompt inside Codex after placing this file in the repo:

```text
Please read this file completely:
Data_Hermetica_Agent_Runtime_v1_Codex_Build_Plan.md

Then inspect the existing repository structure and current Node.js document pipeline.

Implement Data Hermetica Agent Runtime v1 exactly as described, using additive changes only unless a small package.json or README update is required.

Start with the scaffold, Python requirements, runtime state schema, Node script tool wrapper, LangGraph graph, CLI runner, validation inspection, exception routing, audit outputs, eval harness, and documentation updates.

Preserve the existing deterministic pipeline. Do not rewrite the Node scripts. Treat them as tool nodes called by the agent runtime.

After implementation, run:

npm run pipeline:run
npm run agent:run
npm run agent:eval

Then report what passed, what failed, which files were changed, and what remains.
```

---

## 27. Final Success Definition

This week is successful when the repo can honestly be described as:

```text
A local-first private document intelligence pipeline upgraded with an experimental agentic runtime layer that uses graph orchestration, persistent run state, deterministic tool execution, validation-driven routing, human-review exception artifacts, audit logging, and evaluation checks.
```

This is Data Hermetica Agent Runtime v1.
