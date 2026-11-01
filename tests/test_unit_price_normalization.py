from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "app"))

from invoice_worker import (  # noqa: E402
    ValidationFailure,
    normalize_unit_prices,
    parse_unit_price_expression,
    write_outputs,
)


class UnitPriceParsingTests(unittest.TestCase):
    def test_slash_unit(self) -> None:
        self.assertEqual(
            parse_unit_price_expression("11.1542 / EA", "test"),
            {
                "unit_price_usd": "11.1542",
                "unit_price_raw": "11.1542 / EA",
                "price_basis_quantity": "1",
                "price_basis_unit": "EA",
            },
        )

    def test_no_basis(self) -> None:
        self.assertEqual(
            parse_unit_price_expression("11.1542", "test"),
            {
                "unit_price_usd": "11.1542",
                "unit_price_raw": "11.1542",
                "price_basis_quantity": None,
                "price_basis_unit": None,
            },
        )

    def test_explicit_basis_quantity(self) -> None:
        parsed = parse_unit_price_expression("250.00 / 100 KG", "test")
        self.assertEqual(parsed["unit_price_usd"], "250.00")
        self.assertEqual(parsed["price_basis_quantity"], "100")
        self.assertEqual(parsed["price_basis_unit"], "KG")

    def test_currency_notation(self) -> None:
        parsed = parse_unit_price_expression("USD 1,234.5678 / EA", "test")
        self.assertEqual(parsed["unit_price_usd"], "1234.5678")

    def test_decimal_comma(self) -> None:
        parsed = parse_unit_price_expression("7,48 / EA", "test")
        self.assertEqual(parsed["unit_price_usd"], "7.48")

    def test_ambiguous_comma_is_rejected(self) -> None:
        with self.assertRaises(ValidationFailure):
            parse_unit_price_expression("1,234 / EA", "test")


class OutputTests(unittest.TestCase):
    def test_legacy_value_becomes_numeric_csv_and_lossless_json(self) -> None:
        result = {
            "invoices": [
                {
                    "invoice_details": {
                        "invoice_number": "TEST-1",
                        "invoice_date": "10/30/2026",
                        "customer_number": "C1",
                        "ship_to": "Ship To",
                        "bill_to": "Bill To",
                        "shipper_details": "Shipper",
                    },
                    "merchandise_items": [
                        {
                            "item": "1",
                            "product_number": "10184784",
                            "material_description": "Nitric acid solution",
                            "unit": "EA",
                            "quantity": "12.000",
                            "unit_price_usd": "11.1542 / EA",
                            "total_amount_usd": "133.85",
                            "country_of_origin": "Germany",
                            "delivery_note": "88590439",
                            "gross_weight": "1,152 KG",
                            "net_weight": "0,720 KG",
                            "commodity_code": "28080000",
                            "shipment_number": "7000373285",
                        }
                    ],
                }
            ]
        }
        normalize_unit_prices(result)
        item = result["invoices"][0]["merchandise_items"][0]
        self.assertEqual(item["unit_price_usd"], "11.1542")
        self.assertEqual(item["unit_price_raw"], "11.1542 / EA")
        self.assertEqual(item["price_basis_quantity"], "1")
        self.assertEqual(item["price_basis_unit"], "EA")

        with tempfile.TemporaryDirectory() as temp_directory:
            outputs = write_outputs(Path(temp_directory), result)
            csv_path = next(path for path in outputs if path.suffix == ".csv")
            with csv_path.open(encoding="utf-8-sig", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual(row["Unit Price (USD)"], "11.1542")


if __name__ == "__main__":
    unittest.main()
