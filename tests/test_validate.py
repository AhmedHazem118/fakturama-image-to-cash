"""Run:  python -m unittest discover -s tests -v   (no network, no Fakturama needed)

Reference data: the task's own example order (samples/task_example_order.expected.json)."""
import copy
import json
import unittest
from decimal import Decimal

from fakturama_bot.validate import fakturama_date, gross_price, line_price, normalize_date, validate

GOOD = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))


def bad(mutate):
    order = copy.deepcopy(GOOD)
    mutate(order)
    return validate(order)


class ValidateTests(unittest.TestCase):
    def test_sample_passes(self):
        v = validate(GOOD)
        self.assertTrue(v.ok, v.errors)
        self.assertEqual(v.order["items"][0]["line_total"], Decimal("450.0"))

    def test_wrong_line_total_is_caught(self):  # e.g. the LLM misread 450.00 as 480.00
        v = bad(lambda o: o["items"][0].update(line_total=480.00))
        self.assertFalse(v.ok)
        self.assertTrue(any("line total" in e for e in v.errors))

    def test_wrong_grand_total_is_caught(self):
        self.assertFalse(bad(lambda o: o["totals"].update(gross=999.99)).ok)

    def test_missing_sku_stops(self):
        self.assertFalse(bad(lambda o: o["items"][1].update(sku=None)).ok)

    def test_duplicate_sku_stops(self):
        self.assertFalse(bad(lambda o: o["items"][1].update(sku=GOOD["items"][0]["sku"])).ok)

    def test_unknown_payment_method_stops(self):
        self.assertFalse(bad(lambda o: o["payment"].update(method="Bitcoin")).ok)

    def test_paid_without_date_stops(self):
        self.assertFalse(bad(lambda o: o["payment"].update(payment_date=None)).ok)

    def test_unpaid_drops_date(self):  # never invent a payment date
        v = bad(lambda o: o["payment"].update(status="UNPAID"))
        self.assertTrue(v.ok)
        self.assertIsNone(v.order["payment"]["payment_date"])

    def test_missing_discount_means_zero(self):
        v = bad(lambda o: o["items"][1].update(discount_percent=None))
        self.assertTrue(v.ok, v.errors)

    def test_dates(self):
        self.assertEqual(normalize_date("2026-07-14"), "2026-07-14")
        self.assertEqual(normalize_date("14 Jul 2026"), "2026-07-14")
        self.assertEqual(normalize_date("Jul 14, 2026"), "2026-07-14")
        self.assertEqual(normalize_date("14.07.2026"), "2026-07-14")
        self.assertEqual(normalize_date("25/07/2026"), "2026-07-25")  # only one reading possible
        self.assertIsNone(normalize_date("05/07/2026"))                # ambiguous: refuse to guess
        self.assertIsNone(normalize_date("tomorrow"))
        self.assertEqual(fakturama_date("2026-07-14"), "Jul 14, 2026")

    def test_money_math(self):
        self.assertEqual(gross_price(Decimal("250"), Decimal("19")), Decimal("297.50"))
        self.assertEqual(gross_price(Decimal("40"), Decimal("19")), Decimal("47.60"))
        self.assertEqual(gross_price(Decimal("30"), Decimal("7")), Decimal("32.10"))   # a reduced rate
        self.assertEqual(line_price(Decimal("2"), Decimal("250"), Decimal("10")), Decimal("450.00"))
        self.assertEqual(line_price(Decimal("3"), Decimal("40"), Decimal("0")), Decimal("120.00"))


if __name__ == "__main__":
    unittest.main()
