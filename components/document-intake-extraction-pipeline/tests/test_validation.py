"""Deterministic validation tests. None of them calls a model or a local service."""

from __future__ import annotations

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from document_pipeline.worker import (
    ITEM_FIELDS,
    ValidationFailure,
    business_validation,
    candidate_item_numbers,
    estimate_tokens,
    normalize_decimal_string,
    normalize_unit_prices,
    validate_schema,
    write_outputs,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (REPOSITORY_ROOT / "config" / "extraction_schema.json").read_text(encoding="utf-8")
)
SAMPLE = REPOSITORY_ROOT / "samples"

SOURCE_TEXT = """
Item  Material   Unit  Quantity   Unit Price        Amount
1     90418277   EA    12.000     6.2500 / EA        75.00
2     90418301   EA     4.000    42.7500 / EA       171.00
3     90527114   KG    25.000     6.3040 / KG       157.60
"""


def sample_extraction() -> dict:
    return json.loads((SAMPLE / "expected" / "extraction.json").read_text(encoding="utf-8"))


class DecimalNormalizationTests(unittest.TestCase):
    def test_ambiguous_single_comma_group_is_rejected(self) -> None:
        with self.assertRaises(ValidationFailure):
            normalize_decimal_string("1,234", "price")

    def test_unambiguous_notations_are_canonicalized(self) -> None:
        self.assertEqual(normalize_decimal_string("1,234.50", "price"), "1234.50")
        self.assertEqual(normalize_decimal_string("1.234,50", "price"), "1234.50")
        self.assertEqual(normalize_decimal_string("7,48", "price"), "7.48")
        self.assertEqual(normalize_decimal_string("1,234,567", "price"), "1234567")

    def test_non_numeric_text_is_rejected(self) -> None:
        with self.assertRaises(ValidationFailure):
            normalize_decimal_string("n/a", "price")


class SchemaValidatorTests(unittest.TestCase):
    def test_sample_extraction_is_valid(self) -> None:
        self.assertEqual(validate_schema(sample_extraction(), SCHEMA), [])

    def test_extra_property_is_rejected(self) -> None:
        result = sample_extraction()
        result["invoices"][0]["merchandise_items"][0]["hts_code"] = "2815120000"
        errors = validate_schema(result, SCHEMA)
        self.assertEqual(len(errors), 1)
        self.assertIn("unexpected property 'hts_code'", errors[0])

    def test_missing_required_property_is_rejected(self) -> None:
        result = sample_extraction()
        del result["invoices"][0]["invoice_details"]["bill_to"]
        self.assertTrue(
            any("missing required property 'bill_to'" in e for e in validate_schema(result, SCHEMA))
        )

    def test_non_canonical_unit_price_is_rejected(self) -> None:
        result = sample_extraction()
        result["invoices"][0]["merchandise_items"][0]["unit_price_usd"] = "6.2500 / EA"
        self.assertTrue(any("does not match pattern" in e for e in validate_schema(result, SCHEMA)))

    def test_empty_invoice_list_is_rejected(self) -> None:
        self.assertTrue(
            any("at least 1 items" in e for e in validate_schema({"invoices": []}, SCHEMA))
        )


class CompletenessTests(unittest.TestCase):
    def test_printed_item_numbers_are_detected(self) -> None:
        self.assertEqual(candidate_item_numbers(SOURCE_TEXT), {"1", "2", "3"})

    def test_complete_extraction_has_no_issues(self) -> None:
        self.assertEqual(business_validation(sample_extraction(), SOURCE_TEXT), [])

    def test_missing_item_is_reported(self) -> None:
        result = sample_extraction()
        del result["invoices"][0]["merchandise_items"][1]
        issues = business_validation(result, SOURCE_TEXT)
        self.assertEqual(len(issues), 1)
        self.assertIn("missing printed items: 2", issues[0])

    def test_duplicate_item_number_is_reported(self) -> None:
        result = sample_extraction()
        items = result["invoices"][0]["merchandise_items"]
        items.append(copy.deepcopy(items[0]))
        self.assertTrue(
            any("duplicate item number '1'" in i for i in business_validation(result, SOURCE_TEXT))
        )

    def test_half_populated_price_basis_is_reported(self) -> None:
        result = sample_extraction()
        result["invoices"][0]["merchandise_items"][0]["price_basis_unit"] = None
        self.assertTrue(any("price basis" in i for i in business_validation(result, SOURCE_TEXT)))


class UnitPriceConflictTests(unittest.TestCase):
    def test_price_conflicting_with_raw_expression_is_rejected(self) -> None:
        result = sample_extraction()
        result["invoices"][0]["merchandise_items"][0]["unit_price_usd"] = "6.2600"
        with self.assertRaises(ValidationFailure):
            normalize_unit_prices(result)

    def test_null_price_clears_basis_fields(self) -> None:
        result = sample_extraction()
        item = result["invoices"][0]["merchandise_items"][0]
        item["unit_price_usd"] = None
        normalize_unit_prices(result)
        self.assertIsNone(item["unit_price_raw"])
        self.assertIsNone(item["price_basis_quantity"])
        self.assertIsNone(item["price_basis_unit"])


class OutputContractTests(unittest.TestCase):
    def test_csv_has_the_thirteen_approved_columns(self) -> None:
        self.assertEqual(len(ITEM_FIELDS), 13)
        with tempfile.TemporaryDirectory() as folder:
            outputs = write_outputs(Path(folder), sample_extraction())
            csv_path = next(path for path in outputs if path.suffix == ".csv")
            generated = csv_path.read_text(encoding="utf-8-sig")
            with csv_path.open(encoding="utf-8-sig", newline="") as stream:
                header = next(csv.reader(stream))
        self.assertEqual(header, [label for _, label in ITEM_FIELDS])
        expected = (SAMPLE / "expected" / "100245.csv").read_text(encoding="utf-8-sig")
        self.assertEqual(generated.replace("\r\n", "\n"), expected.replace("\r\n", "\n"))

    def test_token_estimate_is_conservative(self) -> None:
        self.assertEqual(estimate_tokens(3000, 2), 1000 + 2 * 4096)


if __name__ == "__main__":
    unittest.main()
