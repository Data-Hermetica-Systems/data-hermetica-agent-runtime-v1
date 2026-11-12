"""Upgrade an existing invoice extraction to the v1.2 canonical price format.

This utility does not call LM Studio. It reads an existing extraction.json,
normalizes unit prices, validates the v1.2 schema, and writes a new complete
JSON/Markdown/CSV output set plus an auditable normalization record.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from document_pipeline.worker import (
    business_validation,
    load_json,
    normalize_unit_prices,
    validate_schema,
    write_json,
    write_outputs,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Existing extraction.json")
    parser.add_argument(
        "--output",
        type=Path,
        help="New output directory; defaults to a normalized_v1_2 sibling directory",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        help="v1.2 schema path; defaults to config/extraction_schema.json in this repository",
    )
    args = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Existing extraction was not found: {input_path}")

    repository_root = Path(__file__).resolve().parents[2]
    schema_path = (
        args.schema.resolve()
        if args.schema
        else repository_root / "config" / "extraction_schema.json"
    )
    output_folder = args.output.resolve() if args.output else input_path.parent / "normalized_v1_2"
    if output_folder == input_path.parent:
        raise RuntimeError(
            "Refusing to overwrite the existing result directory. Choose a new --output directory."
        )

    result = load_json(input_path)
    schema = load_json(schema_path)
    audit = normalize_unit_prices(result)
    issues = validate_schema(result, schema)
    issues.extend(business_validation(result, ""))
    if issues:
        raise RuntimeError("\n".join(["v1.2 validation failed:", *issues]))

    outputs = write_outputs(output_folder, result)
    normalization_path = output_folder / "unit-price-normalization.json"
    write_json(
        normalization_path,
        {
            "normalized_at": utc_now(),
            "source_extraction": str(input_path),
            "items": audit,
        },
    )
    outputs.append(normalization_path)

    validation_path = output_folder / "validation.json"
    merchandise_count = sum(len(invoice["merchandise_items"]) for invoice in result["invoices"])
    write_json(
        validation_path,
        {
            "status": "passed",
            "validated_at": utc_now(),
            "migration": "v1.1-to-v1.2-unit-price-normalization",
            "invoice_count": len(result["invoices"]),
            "merchandise_row_count": merchandise_count,
            "issues": [],
        },
    )
    outputs.append(validation_path)

    print("Status: COMPLETED")
    print(f"Merchandise rows: {merchandise_count}")
    print(f"Output directory: {output_folder}")
    for output in outputs:
        print(f"Generated: {output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
