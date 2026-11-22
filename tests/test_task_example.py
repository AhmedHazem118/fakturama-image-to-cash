"""The task's own example order: its answer key must pass the validator with exactly the printed totals."""
import json
import unittest
from decimal import Decimal

from fakturama_bot.validate import validate, gross_price, line_price


class TaskExample(unittest.TestCase):
    def setUp(self):
        with open("samples/task_example_order.expected.json", encoding="utf-8") as fh:
            self.raw = json.load(fh)

    def test_answer_key_is_valid(self):
        result = validate(self.raw)
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.order["order_date"], "2026-07-14")
        self.assertEqual(result.order["payment"]["payment_date"], "2026-07-18")
        self.assertEqual(result.order["totals"]["gross"], Decimal("678.3"))

    def test_line_and_gross_arithmetic(self):
        self.assertEqual(line_price(Decimal(2), Decimal(250), Decimal(10)), Decimal("450.00"))
        self.assertEqual(line_price(Decimal(3), Decimal(40), Decimal(0)), Decimal("120.00"))
        self.assertEqual(gross_price(Decimal(250), Decimal(19)), Decimal("297.50"))
        self.assertEqual(gross_price(Decimal(40), Decimal(19)), Decimal("47.60"))

    def test_new_fields_pass_through(self):
        order = validate(self.raw).order
        self.assertEqual(order["customer_id"], "CUST-1007")
        self.assertEqual(order["currency"], "EUR")
        self.assertEqual(order["debtor"]["delivery"]["street"], "Beusselstrasse 44")
        self.assertEqual(order["items"][0]["unit"], "pcs")

    def test_wrong_total_is_caught(self):
        self.raw["totals"]["net"] = 571.0
        self.assertFalse(validate(self.raw).ok)


if __name__ == "__main__":
    unittest.main()
