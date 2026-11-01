"""Run one prepared invoice through LM Studio as one full-document request.

The worker never batches merchandise items. It records durable job state in
SQLite, saves an auditable request/response trail, enforces JSON Schema output,
validates the extraction, and renders JSON, Markdown, and CSV results.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import math
import mimetypes
import os
import re
import shutil
import sqlite3
import sys
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DETAIL_FIELDS = [
    ("invoice_number", "Invoice Number"),
    ("invoice_date", "Invoice Date"),
    ("customer_number", "Customer No."),
    ("ship_to", "Ship To"),
    ("bill_to", "Bill To"),
    ("shipper_details", "Shipper Details"),
]

ITEM_FIELDS = [
    ("item", "Item"),
    ("product_number", "Product Number"),
    ("material_description", "Material Description"),
    ("unit", "Unit"),
    ("quantity", "Quantity"),
    ("unit_price_usd", "Unit Price (USD)"),
    ("total_amount_usd", "Total Amount (USD)"),
    ("country_of_origin", "Country of Origin"),
    ("delivery_note", "Delivery Note"),
    ("gross_weight", "Gross Weight"),
    ("net_weight", "Net Weight"),
    ("commodity_code", "Commodity Code"),
    ("shipment_number", "Shipment Number"),
]

CANONICAL_DECIMAL_PATTERN = re.compile(r"^\d+(?:\.\d+)?$")

PRODUCTION_OUTPUT_OVERRIDE = """PRODUCTION API SERIALIZATION OVERRIDE

For this API request, the response_format JSON Schema is the sole output
format. Do not output Markdown, headings, commentary, code fences, or prose.
Populate the JSON fields using all extraction definitions and source-fidelity
rules below. Instructions below that request Markdown tables are superseded
only with respect to serialization. Their field definitions, source rules,
item-boundary rules, cleaning rules, and final checks remain authoritative.
Use JSON null for unresolved values and JSON strings for source values.
"""

USER_INSTRUCTION = """Extract every invoice and every merchandise item from
all supplied source pages. Read the pages in source order, join item
continuations across page breaks, keep repeated products as separate rows, and
associate every field with its correct invoice and item. Return only the JSON
object required by the response schema.
"""


class ValidationFailure(RuntimeError):
    """The model response was syntactically valid but failed deterministic checks."""


class ContextBudgetFailure(RuntimeError):
    """The full-document request cannot fit the configured context budget."""


class RuntimeConfigurationFailure(RuntimeError):
    """LM Studio is not configured for deterministic invoice extraction."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def engine_root() -> Path:
    configured = os.environ.get("DATA_HERMETICA_INVOICE_ENGINE_ROOT")
    if not configured:
        raise RuntimeError(
            "DATA_HERMETICA_INVOICE_ENGINE_ROOT is missing. "
            "Expected H:\\DataHermetica\\InvoiceEngine"
        )
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        raise RuntimeError(f"Engine root does not exist: {root}")
    return root


def locate_manifest(root: Path, explicit: Path | None, digest: str | None) -> Path:
    prepared = root / "work" / "prepared"
    if explicit is not None:
        manifest = explicit.expanduser().resolve()
    elif digest:
        manifest = prepared / digest / "manifest.json"
    else:
        candidates = list(prepared.glob("*/manifest.json"))
        if not candidates:
            raise FileNotFoundError(f"No prepared manifests found in {prepared}")
        manifest = max(candidates, key=lambda value: value.stat().st_mtime_ns)
    if not manifest.is_file():
        raise FileNotFoundError(f"Manifest does not exist: {manifest}")
    return manifest


def open_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            document_sha256 TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            status TEXT NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            model TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            request_path TEXT,
            response_path TEXT,
            result_path TEXT,
            error_message TEXT
        )
        """
    )
    connection.commit()
    return connection


def register_job(
    connection: sqlite3.Connection,
    digest: str,
    source_file: str,
    model: str,
    force: bool,
) -> None:
    row = connection.execute(
        "SELECT status FROM jobs WHERE document_sha256 = ?", (digest,)
    ).fetchone()
    if row and row["status"] == "COMPLETED" and not force:
        raise RuntimeError(
            f"Document {digest} is already COMPLETED. Use --force to rerun it."
        )
    timestamp = utc_now()
    with connection:
        connection.execute(
            """
            INSERT INTO jobs (
                document_sha256, source_file, status, attempt_count, model,
                created_at, updated_at, error_message
            ) VALUES (?, ?, 'READY', 0, ?, ?, ?, NULL)
            ON CONFLICT(document_sha256) DO UPDATE SET
                source_file = excluded.source_file,
                status = 'READY',
                model = excluded.model,
                updated_at = excluded.updated_at,
                error_message = NULL
            """,
            (digest, source_file, model, timestamp, timestamp),
        )


def update_job(
    connection: sqlite3.Connection,
    digest: str,
    status: str,
    *,
    request_path: Path | None = None,
    response_path: Path | None = None,
    result_path: Path | None = None,
    error_message: str | None = None,
    increment_attempt: bool = False,
) -> None:
    with connection:
        connection.execute(
            """
            UPDATE jobs SET
                status = ?,
                updated_at = ?,
                request_path = COALESCE(?, request_path),
                response_path = COALESCE(?, response_path),
                result_path = COALESCE(?, result_path),
                error_message = ?,
                attempt_count = attempt_count + ?
            WHERE document_sha256 = ?
            """,
            (
                status,
                utc_now(),
                str(request_path) if request_path else None,
                str(response_path) if response_path else None,
                str(result_path) if result_path else None,
                error_message,
                1 if increment_attempt else 0,
                digest,
            ),
        )


def data_url(path: Path) -> str:
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def assemble_document(
    manifest_path: Path, manifest: dict[str, Any]
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    folder = manifest_path.parent
    pages = manifest.get("pages")
    if not isinstance(pages, list) or not pages:
        raise RuntimeError("Manifest contains no pages")

    content: list[dict[str, Any]] = []
    complete_text_parts: list[str] = []
    image_audit: list[dict[str, Any]] = []

    for page in sorted(pages, key=lambda value: int(value["page"])):
        number = int(page["page"])
        text_name = page.get("text_file")
        image_name = page.get("image_file")
        page_text = ""

        if text_name:
            text_path = folder / str(text_name)
            if not text_path.is_file():
                raise RuntimeError(f"Missing prepared text file: {text_path}")
            page_text = text_path.read_text(encoding="utf-8", errors="replace")

        marked_text = (
            f"\n[SOURCE PAGE {number} START]\n"
            f"{page_text}\n"
            f"[SOURCE PAGE {number} END]\n"
        )
        content.append({"type": "text", "text": marked_text})
        complete_text_parts.append(marked_text)

        if image_name:
            image_path = folder / str(image_name)
            if not image_path.is_file():
                raise RuntimeError(f"Missing prepared image file: {image_path}")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_url(image_path)},
                }
            )
            image_audit.append(
                {
                    "page": number,
                    "file": str(image_path),
                    "sha256": sha256_file(image_path),
                    "size_bytes": image_path.stat().st_size,
                }
            )

    return content, "".join(complete_text_parts), image_audit


def estimate_tokens(text_characters: int, image_count: int) -> int:
    conservative_text_tokens = math.ceil(text_characters / 3)
    conservative_image_tokens = image_count * 4096
    return conservative_text_tokens + conservative_image_tokens


def http_json(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("LM_STUDIO_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"LM Studio returned HTTP {exc.code} for {url}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach LM Studio at {url}: {exc.reason}") from exc
    try:
        value = json.loads(response_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LM Studio returned invalid JSON: {response_body[:1000]}") from exc
    if not isinstance(value, dict):
        raise RuntimeError("LM Studio returned a non-object JSON response")
    return value


def verify_model(base_url: str, model: str, timeout: int) -> None:
    response = http_json("GET", f"{base_url.rstrip('/')}/models", timeout=timeout)
    models = response.get("data")
    identifiers = {
        item.get("id") for item in models if isinstance(item, dict) and item.get("id")
    } if isinstance(models, list) else set()
    if model not in identifiers:
        raise RuntimeError(
            f"Configured model {model!r} is not available. LM Studio reported: "
            f"{sorted(identifiers)}"
        )


def response_text(api_response: dict[str, Any]) -> str:
    try:
        content = api_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LM Studio response has no assistant message content") from exc
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                fragments.append(part["text"])
        if fragments:
            return "".join(fragments)
    raise RuntimeError("LM Studio returned unsupported assistant content")


def response_finish_reason(api_response: dict[str, Any]) -> str | None:
    try:
        value = api_response["choices"][0].get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        return None
    return str(value) if value is not None else None


def response_reasoning_tokens(api_response: dict[str, Any]) -> int:
    usage = api_response.get("usage")
    if not isinstance(usage, dict):
        return 0
    details = usage.get("completion_tokens_details")
    if not isinstance(details, dict):
        return 0
    value = details.get("reasoning_tokens", 0)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def response_reasoning_characters(api_response: dict[str, Any]) -> int:
    try:
        message = api_response["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        return 0
    if not isinstance(message, dict):
        return 0
    for key in ("reasoning_content", "reasoning"):
        value = message.get(key)
        if isinstance(value, str):
            return len(value)
    return 0


def build_sampling_parameters(config: dict[str, Any]) -> dict[str, int | float]:
    """Build explicit LM Studio inference parameters from engine_config.json."""
    return {
        "temperature": float(config["temperature"]),
        "top_p": float(config["top_p"]),
        "top_k": int(config["top_k"]),
        "presence_penalty": float(config["presence_penalty"]),
        "repeat_penalty": float(config["repeat_penalty"]),
    }


def verify_extraction_runtime(
    base_url: str,
    model: str,
    timeout: int,
    max_tokens: int,
    sampling_parameters: dict[str, int | float],
) -> dict[str, Any]:
    """Verify that the loaded model emits final structured content directly."""
    preflight_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["status"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["ready"],
            }
        },
    }
    payload = {
        "model": model,
        **sampling_parameters,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return the required JSON object immediately. "
                    "Do not reason, explain, or add commentary."
                ),
            },
            {
                "role": "user",
                "content": "Set status to ready.",
            },
        ],
        "max_tokens": max_tokens,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "data_hermetica_runtime_preflight",
                "strict": True,
                "schema": preflight_schema,
            },
        },
    }
    response = http_json(
        "POST",
        f"{base_url.rstrip('/')}/chat/completions",
        payload=payload,
        timeout=timeout,
    )
    content = response_text(response)
    reasoning_tokens = response_reasoning_tokens(response)
    reasoning_characters = response_reasoning_characters(response)
    finish_reason = response_finish_reason(response)

    if reasoning_tokens > 0 or reasoning_characters > 0 or not content.strip():
        raise RuntimeConfigurationFailure(
            "LM Studio extraction preflight failed: the loaded model generated "
            f"{reasoning_tokens} reasoning tokens / {reasoning_characters} reasoning "
            f"characters, final content length {len(content)}, finish reason "
            f"{finish_reason!r}. In LM Studio, open the loaded Qwen 3.8 27B model's "
            "Inference settings, turn Enable Thinking OFF and Preserve Thinking OFF, "
            "then reload the model before retrying. The invoice was not submitted."
        )

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeConfigurationFailure(
            "LM Studio extraction preflight returned non-JSON final content. "
            "Reload the model with Enable Thinking OFF before retrying."
        ) from exc
    if parsed != {"status": "ready"}:
        raise RuntimeConfigurationFailure(
            "LM Studio extraction preflight did not satisfy the required test schema: "
            f"{parsed!r}"
        )
    return response


def validate_schema(value: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]

    def matches(type_name: str | None) -> bool:
        if type_name == "null":
            return value is None
        if type_name == "object":
            return isinstance(value, dict)
        if type_name == "array":
            return isinstance(value, list)
        if type_name == "string":
            return isinstance(value, str)
        if type_name == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        if type_name == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        if type_name == "boolean":
            return isinstance(value, bool)
        return True

    if expected_type is not None and not any(matches(name) for name in allowed_types):
        return [f"{path}: value does not match type {expected_type!r}"]

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}: unexpected property {key!r}")
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(validate_schema(value[key], child_schema, f"{path}.{key}"))

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: expected at least {minimum} items, found {len(value)}")
        child_schema = schema.get("items")
        if isinstance(child_schema, dict):
            for index, child in enumerate(value):
                errors.extend(validate_schema(child, child_schema, f"{path}[{index}]"))

    if isinstance(value, str):
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.fullmatch(pattern, value) is None:
            errors.append(f"{path}: value does not match pattern {pattern!r}")

    return errors


def normalize_decimal_string(value: str, field_name: str) -> str:
    """Convert an unambiguous printed decimal to canonical period notation.

    Thousands separators are removed only when the notation is structurally
    unambiguous. A lone comma followed by exactly three digits is rejected
    because it could mean either a thousands separator or a decimal separator.
    """
    text = value.strip().replace(" ", "").replace("'", "").replace("’", "")
    if not text or re.fullmatch(r"\d[\d.,]*", text) is None:
        raise ValidationFailure(f"{field_name} is not a valid decimal: {value!r}")

    if "," in text and "." in text:
        decimal_separator = "," if text.rfind(",") > text.rfind(".") else "."
        thousands_separator = "." if decimal_separator == "," else ","
        text = text.replace(thousands_separator, "")
        if decimal_separator == ",":
            text = text.replace(",", ".")
    elif "," in text:
        groups = text.split(",")
        if len(groups) == 2:
            if len(groups[1]) == 3:
                raise ValidationFailure(
                    f"{field_name} has ambiguous comma notation: {value!r}"
                )
            text = groups[0] + "." + groups[1]
        elif all(len(group) == 3 for group in groups[1:]):
            text = "".join(groups)
        elif all(len(group) == 3 for group in groups[1:-1]):
            text = "".join(groups[:-1]) + "." + groups[-1]
        else:
            raise ValidationFailure(
                f"{field_name} has invalid comma grouping: {value!r}"
            )

    if CANONICAL_DECIMAL_PATTERN.fullmatch(text) is None:
        raise ValidationFailure(
            f"{field_name} could not be normalized to a canonical decimal: {value!r}"
        )
    return text


def parse_unit_price_expression(value: str, field_name: str) -> dict[str, str | None]:
    """Parse a printed unit-price expression without discarding price basis."""
    raw = value.strip()
    if not raw:
        raise ValidationFailure(f"{field_name} is empty")
    if raw.count("/") > 1:
        raise ValidationFailure(f"{field_name} contains multiple '/' separators: {raw!r}")

    price_part, separator, basis_part = raw.partition("/")
    price_part = price_part.strip()
    price_part = re.sub(r"^(?:USD|US\$|\$)\s*", "", price_part, flags=re.IGNORECASE)
    price_part = re.sub(r"\s*(?:USD|US\$)$", "", price_part, flags=re.IGNORECASE)
    unit_price = normalize_decimal_string(price_part, field_name)

    basis_quantity: str | None = None
    basis_unit: str | None = None
    if separator:
        basis = basis_part.strip()
        match = re.fullmatch(r"(?:(\d[\d.,]*)\s*)?([A-Za-z][A-Za-z0-9._-]*)", basis)
        if match is None:
            raise ValidationFailure(f"{field_name} has an invalid price basis: {basis!r}")
        printed_quantity, printed_unit = match.groups()
        basis_quantity = (
            normalize_decimal_string(printed_quantity, field_name + " basis quantity")
            if printed_quantity
            else "1"
        )
        basis_unit = printed_unit.upper()

    return {
        "unit_price_usd": unit_price,
        "unit_price_raw": raw,
        "price_basis_quantity": basis_quantity,
        "price_basis_unit": basis_unit,
    }


def normalize_unit_prices(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Canonicalize unit prices and return an auditable transformation log."""
    audit: list[dict[str, Any]] = []
    for invoice_index, invoice in enumerate(result.get("invoices", []), start=1):
        for item_index, item in enumerate(invoice.get("merchandise_items", []), start=1):
            supplied_price = item.get("unit_price_usd")
            supplied_raw = item.get("unit_price_raw")
            supplied_basis_quantity = item.get("price_basis_quantity")
            supplied_basis_unit = item.get("price_basis_unit")

            if supplied_price is None:
                item["unit_price_raw"] = None
                item["price_basis_quantity"] = None
                item["price_basis_unit"] = None
                continue
            if not isinstance(supplied_price, str):
                raise ValidationFailure(
                    f"Invoice {invoice_index} item {item_index}: unit_price_usd must be a string or null"
                )

            source_expression = (
                supplied_raw
                if isinstance(supplied_raw, str) and supplied_raw.strip()
                else supplied_price
            )
            parsed_source = parse_unit_price_expression(
                source_expression,
                f"Invoice {invoice_index} item {item_index} unit price",
            )
            parsed_supplied = parse_unit_price_expression(
                supplied_price,
                f"Invoice {invoice_index} item {item_index} unit_price_usd",
            )

            canonical_price = parsed_supplied["unit_price_usd"]
            if parsed_source["unit_price_usd"] != canonical_price:
                raise ValidationFailure(
                    f"Invoice {invoice_index} item {item_index}: unit_price_usd "
                    f"{canonical_price!r} conflicts with unit_price_raw {source_expression!r}"
                )

            parsed_basis_quantity = parsed_source["price_basis_quantity"]
            parsed_basis_unit = parsed_source["price_basis_unit"]
            if parsed_basis_unit is None:
                parsed_basis_quantity = (
                    normalize_decimal_string(
                        supplied_basis_quantity,
                        f"Invoice {invoice_index} item {item_index} price basis quantity",
                    )
                    if isinstance(supplied_basis_quantity, str)
                    else None
                )
                parsed_basis_unit = (
                    supplied_basis_unit.strip().upper()
                    if isinstance(supplied_basis_unit, str) and supplied_basis_unit.strip()
                    else None
                )
                if parsed_basis_unit is not None and parsed_basis_quantity is None:
                    parsed_basis_quantity = "1"

            before = {
                "unit_price_usd": supplied_price,
                "unit_price_raw": supplied_raw,
                "price_basis_quantity": supplied_basis_quantity,
                "price_basis_unit": supplied_basis_unit,
            }
            item.update(
                {
                    "unit_price_usd": canonical_price,
                    "unit_price_raw": source_expression,
                    "price_basis_quantity": parsed_basis_quantity,
                    "price_basis_unit": parsed_basis_unit,
                }
            )
            after = {
                "unit_price_usd": item["unit_price_usd"],
                "unit_price_raw": item["unit_price_raw"],
                "price_basis_quantity": item["price_basis_quantity"],
                "price_basis_unit": item["price_basis_unit"],
            }
            audit.append(
                {
                    "invoice_index": invoice_index,
                    "item": item.get("item"),
                    "before": before,
                    "after": after,
                    "changed": before != after,
                }
            )
    return audit


def candidate_item_numbers(source_text: str) -> set[str]:
    pattern = re.compile(
        r"(?m)^\s*(\d{1,5})\s*(?:\([^)]+\)\s*)?(?:XX\s*)?\d{6,14}(?=\s|[A-Z])"
    )
    return {match.group(1) for match in pattern.finditer(source_text)}


def business_validation(result: dict[str, Any], source_text: str) -> list[str]:
    issues: list[str] = []
    invoices = result.get("invoices", [])
    extracted_items: list[str] = []
    for invoice_index, invoice in enumerate(invoices):
        seen: set[str] = set()
        for item in invoice.get("merchandise_items", []):
            number = item.get("item")
            if isinstance(number, str) and number:
                extracted_items.append(number)
                if number in seen:
                    issues.append(
                        f"Invoice {invoice_index + 1}: duplicate item number {number!r}"
                    )
                seen.add(number)
            unit_price = item.get("unit_price_usd")
            if unit_price is not None and (
                not isinstance(unit_price, str)
                or CANONICAL_DECIMAL_PATTERN.fullmatch(unit_price) is None
            ):
                issues.append(
                    f"Invoice {invoice_index + 1} item {number!r}: Unit Price (USD) "
                    "must contain only a canonical decimal number"
                )
            basis_quantity = item.get("price_basis_quantity")
            basis_unit = item.get("price_basis_unit")
            if (basis_quantity is None) != (basis_unit is None):
                issues.append(
                    f"Invoice {invoice_index + 1} item {number!r}: price basis "
                    "quantity and unit must either both be populated or both be null"
                )

    candidates = candidate_item_numbers(source_text)
    if len(candidates) >= 2:
        missing = sorted(candidates - set(extracted_items), key=lambda x: int(x))
        if missing:
            issues.append(
                "Source-pattern completeness check found missing printed items: "
                + ", ".join(missing)
            )
    return issues


def markdown_cell(value: Any) -> str:
    if value is None:
        return "null"
    return str(value).replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def render_markdown(result: dict[str, Any]) -> str:
    lines = ["A. Invoice Details", ""]
    detail_headers = [label for _, label in DETAIL_FIELDS]
    lines.append("| " + " | ".join(detail_headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(detail_headers)) + " |")
    for invoice in result["invoices"]:
        details = invoice["invoice_details"]
        lines.append(
            "| " + " | ".join(markdown_cell(details[key]) for key, _ in DETAIL_FIELDS) + " |"
        )

    for invoice in result["invoices"]:
        invoice_number = invoice["invoice_details"]["invoice_number"]
        lines.extend(["", f"B. Merchandise Items — Invoice {markdown_cell(invoice_number)}", ""])
        headers = [label for _, label in ITEM_FIELDS]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for item in invoice["merchandise_items"]:
            lines.append(
                "| " + " | ".join(markdown_cell(item[key]) for key, _ in ITEM_FIELDS) + " |"
            )
    return "\n".join(lines) + "\n"


def safe_filename(value: Any, fallback: str) -> str:
    text = fallback if value is None else str(value)
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("._")
    return cleaned or fallback


def write_outputs(folder: Path, result: dict[str, Any]) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    json_path = folder / "extraction.json"
    markdown_path = folder / "extraction.md"
    write_json(json_path, result)
    markdown_path.write_text(render_markdown(result), encoding="utf-8")
    outputs.extend([json_path, markdown_path])

    for index, invoice in enumerate(result["invoices"], start=1):
        invoice_number = invoice["invoice_details"]["invoice_number"]
        csv_name = safe_filename(invoice_number, f"invoice-{index}") + ".csv"
        csv_path = folder / csv_name
        with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=[label for _, label in ITEM_FIELDS],
                extrasaction="raise",
            )
            writer.writeheader()
            for item in invoice["merchandise_items"]:
                writer.writerow(
                    {
                        label: "null" if item[key] is None else item[key]
                        for key, label in ITEM_FIELDS
                    }
                )
        outputs.append(csv_path)
    return outputs


def audit_payload(
    payload: dict[str, Any],
    manifest: dict[str, Any],
    images: list[dict[str, Any]],
    token_estimate: int,
) -> dict[str, Any]:
    copied = json.loads(json.dumps(payload))
    for message in copied.get("messages", []):
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    part["image_url"] = {"url": "[BASE64 OMITTED; SEE image_audit]"}
    return {
        "created_at": utc_now(),
        "document_sha256": manifest.get("sha256"),
        "source_file": manifest.get("source_file"),
        "estimated_input_tokens": token_estimate,
        "image_audit": images,
        "request": copied,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="Prepared manifest to process")
    parser.add_argument("--sha256", help="Prepared document SHA-256 directory to process")
    parser.add_argument("--force", action="store_true", help="Rerun a completed document")
    parser.add_argument("--dry-run", action="store_true", help="Assemble and validate without calling LM Studio")
    args = parser.parse_args()

    root = engine_root()
    config_folder = root / "config"
    config = load_json(config_folder / "engine_config.json")
    sampling_parameters = build_sampling_parameters(config)
    schema = load_json(config_folder / str(config["schema_file"]))
    prompt_path = config_folder / str(config["system_prompt_file"])
    if not prompt_path.is_file():
        raise FileNotFoundError(f"System prompt file does not exist: {prompt_path}")
    baseline_prompt = prompt_path.read_text(encoding="utf-8")
    system_prompt = PRODUCTION_OUTPUT_OVERRIDE + "\n\n" + baseline_prompt

    if config.get("allow_automatic_batching") is not False:
        raise RuntimeError("Production safety check: automatic batching must be false")
    if config.get("require_reasoning_disabled") is not True:
        raise RuntimeError(
            "Production safety check: require_reasoning_disabled must be true"
        )

    manifest_path = locate_manifest(root, args.manifest, args.sha256)
    manifest = load_json(manifest_path)
    digest = str(manifest.get("sha256") or manifest_path.parent.name)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise RuntimeError(f"Manifest has an invalid SHA-256 value: {digest!r}")
    digest = digest.lower()

    database = open_database(root / "state" / "jobs.db")
    request_path = root / "work" / "requests" / f"{digest}.request.json"
    response_path = root / "work" / "responses" / f"{digest}.response.json"
    preflight_path = root / "logs" / f"{digest}.runtime-preflight.json"
    output_folder = root / "work" / "output_staging" / digest
    model = str(config["model"])

    try:
        register_job(
            database,
            digest,
            str(manifest.get("source_file", "")),
            model,
            args.force,
        )
        update_job(database, digest, "PREPARING")

        document_content, source_text, images = assemble_document(manifest_path, manifest)
        user_content: list[dict[str, Any]] = [
            {"type": "text", "text": USER_INSTRUCTION}
        ] + document_content

        request_schema = json.loads(json.dumps(schema))
        request_schema.pop("$schema", None)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            **sampling_parameters,
            "max_tokens": config["max_output_tokens"],
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "data_hermetica_invoice_extraction",
                    "strict": True,
                    "schema": request_schema,
                },
            },
        }

        total_characters = len(system_prompt) + len(USER_INSTRUCTION) + len(source_text)
        token_estimate = estimate_tokens(total_characters, len(images))
        required_budget = (
            token_estimate
            + int(config["max_output_tokens"])
            + int(config["safety_margin_tokens"])
        )
        context_length = int(config["context_length"])
        if required_budget > context_length:
            raise ContextBudgetFailure(
                "Full-document request exceeds the configured context budget: "
                f"estimated input {token_estimate} + maximum output "
                f"{config['max_output_tokens']} + safety margin "
                f"{config['safety_margin_tokens']} = {required_budget}, "
                f"context length = {context_length}. No automatic batching was performed."
            )

        write_json(
            request_path,
            audit_payload(payload, manifest, images, token_estimate),
        )
        update_job(database, digest, "READY", request_path=request_path)

        print(f"Document SHA-256: {digest}")
        print(f"Pages: {manifest.get('page_count')}")
        print(f"Image pages: {len(images)}")
        print(f"Estimated input tokens: {token_estimate}")
        print(f"Reserved maximum output tokens: {config['max_output_tokens']}")
        print(f"Configured context length: {context_length}")
        print("Automatic batching: disabled")

        if args.dry_run:
            print(f"Dry-run request audit: {request_path}")
            return 0

        timeout = int(config["timeout_seconds"])
        base_url = str(config["lm_studio_base_url"]).rstrip("/")
        verify_model(base_url, model, min(timeout, 60))
        preflight_response = verify_extraction_runtime(
            base_url,
            model,
            min(timeout, 60),
            int(config["preflight_max_tokens"]),
            sampling_parameters,
        )
        write_json(preflight_path, preflight_response)
        update_job(database, digest, "EXTRACTING", increment_attempt=True)

        api_response = http_json(
            "POST",
            f"{base_url}/chat/completions",
            payload=payload,
            timeout=timeout,
        )
        write_json(response_path, api_response)
        update_job(database, digest, "VALIDATING", response_path=response_path)

        assistant_text = response_text(api_response)
        finish_reason = response_finish_reason(api_response)
        reasoning_tokens = response_reasoning_tokens(api_response)
        reasoning_characters = response_reasoning_characters(api_response)
        if not assistant_text.strip():
            raise ValidationFailure(
                "LM Studio returned empty final content. "
                f"Finish reason: {finish_reason!r}; reasoning tokens: "
                f"{reasoning_tokens}; reasoning characters: {reasoning_characters}. "
                "The raw response was preserved. Ensure Enable Thinking and Preserve "
                "Thinking are OFF for the loaded extraction model."
            )
        if finish_reason == "length":
            raise ValidationFailure(
                "LM Studio reached the configured completion-token limit before a "
                "complete structured result was returned. The raw response was preserved."
            )
        try:
            result = json.loads(assistant_text)
        except json.JSONDecodeError as exc:
            raise ValidationFailure(
                f"Assistant content is not valid JSON: {assistant_text[:2000]}"
            ) from exc
        if not isinstance(result, dict):
            raise ValidationFailure("Assistant JSON root is not an object")

        normalization_audit = normalize_unit_prices(result)
        issues = validate_schema(result, schema)
        issues.extend(business_validation(result, source_text))
        if issues:
            raise ValidationFailure("\n".join(issues))

        outputs = write_outputs(output_folder, result)
        normalization_path = output_folder / "unit-price-normalization.json"
        write_json(
            normalization_path,
            {
                "normalized_at": utc_now(),
                "document_sha256": digest,
                "items": normalization_audit,
            },
        )
        outputs.append(normalization_path)
        validation_path = output_folder / "validation.json"
        write_json(
            validation_path,
            {
                "status": "passed",
                "validated_at": utc_now(),
                "document_sha256": digest,
                "invoice_count": len(result["invoices"]),
                "merchandise_row_count": sum(
                    len(invoice["merchandise_items"])
                    for invoice in result["invoices"]
                ),
                "candidate_source_items": sorted(
                    candidate_item_numbers(source_text), key=lambda value: int(value)
                ),
                "issues": [],
            },
        )
        outputs.append(validation_path)

        onedrive = os.environ.get("OneDriveCommercial")
        published_folder = None
        if onedrive:
            published_folder = Path(onedrive) / "InvoiceResults" / "Completed" / digest
            published_folder.mkdir(parents=True, exist_ok=True)
            for output in outputs:
                shutil.copy2(output, published_folder / output.name)

        update_job(
            database,
            digest,
            "COMPLETED",
            result_path=published_folder or output_folder,
            error_message=None,
        )
        print(f"Status: COMPLETED")
        print(f"Local results: {output_folder}")
        if published_folder:
            print(f"OneDrive results: {published_folder}")
        return 0

    except (ContextBudgetFailure, RuntimeConfigurationFailure) as exc:
        update_job(database, digest, "REVIEW_REQUIRED", error_message=str(exc))
        configuration_log = root / "logs" / f"{digest}.configuration-error.txt"
        configuration_log.write_text(str(exc), encoding="utf-8")
        raise
    except ValidationFailure as exc:
        review_folder = None
        onedrive = os.environ.get("OneDriveCommercial")
        if onedrive:
            review_folder = Path(onedrive) / "InvoiceResults" / "ReviewRequired" / digest
            review_folder.mkdir(parents=True, exist_ok=True)
            if response_path.is_file():
                shutil.copy2(response_path, review_folder / response_path.name)
            (review_folder / "validation-error.txt").write_text(str(exc), encoding="utf-8")
        update_job(
            database,
            digest,
            "REVIEW_REQUIRED",
            response_path=response_path if response_path.is_file() else None,
            result_path=review_folder,
            error_message=str(exc),
        )
        raise
    except Exception as exc:
        update_job(database, digest, "FAILED", error_message=str(exc))
        failure_log = root / "logs" / f"{digest}.failure.log"
        failure_log.write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        database.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
