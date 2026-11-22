"""Validator: the safety net between the extractor (LLM) and Fakturama.

Pure Python, no UI, no network. Takes the extracted dict and returns:
  - a NORMALIZED order (ISO dates, Decimal money), and
  - a list of problems. Any problem means: stop for manual review.

Money uses Decimal, never float: 0.1 + 0.2 != 0.3 in float, and accounting
must match to the cent.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

ALLOWED_PAYMENT_METHODS = {"Bank Transfer", "Credit Card", "SEPA Direct Debit"}
CENT = Decimal("0.01")
TOLERANCE = Decimal("0.02")  # per-line rounding can differ from the printed total by a cent or two


@dataclass
class Validation:
    order: dict
    errors: list = field(default_factory=list)

    @property
    def ok(self):
        return not self.errors


# ------------------------------------------------------------------ helpers
def money(value):
    """Convert to Decimal safely (via str, so 19.99 does not become 19.989999...)."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def round2(x):
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def line_price(qty, unit_net, discount_percent):
    """qty x unit net x (1 - discount/100), rounded to 2 decimals (task step 3.16)."""
    return round2(qty * unit_net * (1 - discount_percent / Decimal(100)))


def gross_price(unit_net, vat_percent):
    """Product master price: unit net x (1 + VAT/100), 2 decimals (task step 3.9).
    The line discount is NOT applied here."""
    return round2(unit_net * (1 + vat_percent / Decimal(100)))


_DATE_FORMATS = ["%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", "%d.%m.%Y"]


def normalize_date(text):
    """Return YYYY-MM-DD, or None if the text is not a clear date.
    Slash dates like 05/11/2026 are ambiguous (5 Nov or May 11?), so they are
    accepted only when only one reading is possible."""
    if not text:
        return None
    text = text.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    parts = text.replace("-", "/").split("/")
    if len(parts) == 3 and all(p.isdigit() for p in parts) and len(parts[2]) == 4:
        a, b, year = int(parts[0]), int(parts[1]), int(parts[2])
        readings = []
        for day, month in ((a, b), (b, a)):  # day-first, then month-first
            try:
                readings.append(datetime(year, month, day).strftime("%Y-%m-%d"))
            except ValueError:
                pass
        if len(set(readings)) == 1:
            return readings[0]
    return None


def fakturama_date(iso):
    """Format for typing into Fakturama's Date field (it shows e.g. 'Nov 21, 2026')."""
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.strftime('%b')} {d.day}, {d.year}"


# ------------------------------------------------------------------ main check
def validate(raw):
    errors = []
    order = {k: raw.get(k) for k in ("order_date", "external_reference", "customer_id", "currency")}
    order["debtor"] = {k: (v.strip() if isinstance(v, str) else v) for k, v in (raw.get("debtor") or {}).items()}
    pay = dict(raw.get("payment") or {})

    # --- dates
    iso = normalize_date(order["order_date"])
    if iso is None:
        errors.append(f"Order date missing or unclear: {order['order_date']!r}")
    order["order_date"] = iso

    # --- required header / debtor fields (never invented, never guessed)
    if not (order["external_reference"] or "").strip():
        errors.append("External reference is missing")
    for f in ("company", "last_name", "street", "zip", "city", "country"):
        if not order["debtor"].get(f):
            errors.append(f"Debtor {f} is missing")

    # --- payment
    method = (pay.get("method") or "").strip()
    if method not in ALLOWED_PAYMENT_METHODS:
        errors.append(f"Payment method {method!r} is not one of {sorted(ALLOWED_PAYMENT_METHODS)}")
    status = (pay.get("status") or "").strip().upper()
    pay_iso = normalize_date(pay.get("payment_date"))
    if status == "PAID" and pay_iso is None:
        errors.append("Status is PAID but the payment date is missing or unclear")
    if status != "PAID":
        pay_iso = None  # do not invent a date or value for unpaid orders (task step 5.3)
    order["payment"] = {"method": method, "status": status, "payment_date": pay_iso}

    # --- items
    items, seen, net_sum, vat_sum = [], set(), Decimal(0), Decimal(0)
    if not raw.get("items"):
        errors.append("No item rows were extracted")
    for n, it in enumerate(raw.get("items") or [], start=1):
        sku = (it.get("sku") or "").strip()
        qty, net = money(it.get("quantity")), money(it.get("unit_net"))
        vat = money(it.get("vat_percent"))
        disc = money(it.get("discount_percent")) or Decimal(0)  # none printed = 0
        total = money(it.get("line_total"))
        label = f"Item {n} ({sku or '?'})"
        if not sku:
            errors.append(f"{label}: SKU missing")
        if sku in seen:
            errors.append(f"{label}: duplicate SKU, needs manual review")
        seen.add(sku)
        if not (it.get("description") or "").strip():
            errors.append(f"{label}: description missing")
        if qty is None or qty <= 0:
            errors.append(f"{label}: quantity missing or not positive")
        if net is None or net < 0:
            errors.append(f"{label}: unit net price missing or negative")
        if vat is None or not (0 <= vat <= 100):
            errors.append(f"{label}: VAT percent missing or out of range")
        if not (0 <= disc <= 100):
            errors.append(f"{label}: discount out of range")
        if None in (qty, net, vat) or total is None:
            if total is None:
                errors.append(f"{label}: line total missing")
            items.append(None)
            continue
        expected = line_price(qty, net, disc)
        if abs(expected - total) > TOLERANCE:
            errors.append(f"{label}: line total {total} != qty x net x (1-discount) = {expected}")
        net_sum += total
        vat_sum += total * vat / 100
        items.append({"sku": sku, "description": it["description"].strip(), "unit": it.get("unit"), "quantity": qty,
                      "unit_net": net, "vat_percent": vat, "discount_percent": disc, "line_total": total})
    order["items"] = [i for i in items if i]

    # --- order totals
    t = raw.get("totals") or {}
    tn, tv, tg = money(t.get("net")), money(t.get("vat")), money(t.get("gross"))
    if None in (tn, tv, tg):
        errors.append("Source totals (net / vat / gross) are missing")
    else:
        if abs(net_sum - tn) > TOLERANCE:
            errors.append(f"Sum of lines {net_sum} != source net total {tn}")
        if abs(vat_sum - tv) > TOLERANCE:
            errors.append(f"Computed VAT {round2(vat_sum)} != source VAT {tv}")
        if abs(tn + tv - tg) > TOLERANCE:
            errors.append(f"Net {tn} + VAT {tv} != gross {tg}")
    order["totals"] = {"net": tn, "vat": tv, "gross": tg}
    return Validation(order, errors)
