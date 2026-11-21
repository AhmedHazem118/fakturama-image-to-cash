"""Create a FAKE order image + the answer key we expect the extractor to produce.

Run from the project root:  python -m tools.make_sample_order
Outputs: samples/order_sample.png and samples/order_sample.expected.json
All data is invented (no real customer).
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("samples")
OUT.mkdir(exist_ok=True)

ORDER = {
    "order_date": "2026-11-05",
    "external_reference": "PO-2026-0457",
    "debtor": {
        "company": "Blue Harbor Trading GmbH",
        "first_name": "Anna",
        "last_name": "Keller",
        "alias": "BHT",
        "street": "Hafenstrasse 12",
        "zip": "20457",
        "city": "Hamburg",
        "country": "Germany",
        "email": "anna.keller@blueharbor.de",
        "phone": "+49 40 1234567",
    },
    "payment": {"method": "Bank Transfer", "status": "PAID", "payment_date": "2026-11-12"},
    "items": [
        {"sku": "KB-100", "description": "Mechanical Keyboard", "quantity": 2, "unit_net": 50.00, "vat_percent": 19, "discount_percent": 10, "line_total": 90.00},
        {"sku": "MS-220", "description": "Wireless Mouse", "quantity": 3, "unit_net": 20.00, "vat_percent": 19, "discount_percent": 0, "line_total": 60.00},
        {"sku": "MN-330", "description": "Printed User Manual", "quantity": 1, "unit_net": 30.00, "vat_percent": 7, "discount_percent": 0, "line_total": 30.00},
    ],
    "totals": {"net": 180.00, "vat": 30.60, "gross": 210.60},
}
(OUT / "order_sample.expected.json").write_text(json.dumps(ORDER, indent=2), encoding="utf-8")

W, H = 1100, 900
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
f = lambda s, b=False: ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf" if b else r"C:\Windows\Fonts\arial.ttf", s)

d.text((50, 40), "PURCHASE ORDER", font=f(40, True), fill="#1F3864")
d.text((50, 100), f"Order date: 05 Nov 2026", font=f(22), fill="black")
d.text((50, 132), f"Reference: {ORDER['external_reference']}", font=f(22), fill="black")

x = ORDER["debtor"]
d.text((50, 190), "Bill to / Ship to:", font=f(20, True), fill="black")
for i, line in enumerate([
    x["company"], f"Attn: {x['first_name']} {x['last_name']}  (alias: {x['alias']})",
    x["street"], f"{x['zip']} {x['city']}, {x['country']}", f"{x['email']}   Tel {x['phone']}"]):
    d.text((50, 222 + i * 30), line, font=f(20), fill="black")

y0 = 420
cols = [50, 170, 480, 570, 700, 790, 900]
heads = ["SKU", "Description", "Qty", "Unit net", "VAT %", "Disc %", "Total"]
d.rectangle([40, y0 - 8, W - 40, y0 + 34], fill="#E8EEF7")
for cx, h in zip(cols, heads):
    d.text((cx, y0), h, font=f(20, True), fill="black")
for r, it in enumerate(ORDER["items"]):
    y = y0 + 55 + r * 45
    vals = [it["sku"], it["description"], str(it["quantity"]), f"{it['unit_net']:.2f}",
            f"{it['vat_percent']}%", f"{it['discount_percent']}%", f"{it['line_total']:.2f}"]
    for cx, v in zip(cols, vals):
        d.text((cx, y), v, font=f(20), fill="black")
    d.line([40, y + 34, W - 40, y + 34], fill="#CCCCCC")

t = ORDER["totals"]
d.text((700, 640), f"Total net:   {t['net']:.2f} EUR", font=f(22), fill="black")
d.text((700, 675), f"VAT:         {t['vat']:.2f} EUR", font=f(22), fill="black")
d.text((700, 710), f"Total gross: {t['gross']:.2f} EUR", font=f(22, True), fill="black")

p = ORDER["payment"]
d.text((50, 760), f"Payment method: {p['method']}", font=f(22), fill="black")
d.text((50, 795), f"Status: {p['status']}    Paid on: 12 Nov 2026", font=f(22, True), fill="#1B7A1B")

img.save(OUT / "order_sample.png")
print("wrote samples/order_sample.png and samples/order_sample.expected.json")
