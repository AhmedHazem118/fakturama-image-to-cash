"""Caption banners and red boxes for the screenshots the runner took (docs/run_shots -> docs/annotated)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
SRC, DST = Path("docs/run_shots"), Path("docs/annotated"); DST.mkdir(exist_ok=True)
ITEMS = {
 "01_order_header_and_debtor": ("Run step 1: order header (date, Cust.Ref., price mode Net) and the debtor selected in the order", [(378, 312, 755, 362), (721, 180, 875, 207), (376, 253, 756, 280)]),
 "02_order_lines_and_totals": ("Run step 2: quantity 2/3, discount 10%, totals read back = net 570.00, VAT 108.30, total 678.30", [(393, 410, 520, 460), (1270, 410, 1395, 460), (1222, 655, 1450, 805)]),
 "03_documents": ("Run step 3: the saved Order PO000001 is found in Data > Documents (state open, total 678.30)", [(483, 235, 1455, 260)]),
 "04_invoice_paid": ("Run step 4: follow-up Invoice: paid, Bank Transfer, paid date Jul 18 2026, value 678.30", [(298, 750, 750, 785)]),
 "05_documents": ("Run step 5: Invoice INV000001 paid and Order PO000001 still open, both 678.30", [(483, 235, 1455, 285)]),
}
font = ImageFont.truetype("arial.ttf", 20)
for name, (caption, boxes) in ITEMS.items():
    im = Image.open(SRC / f"{name}.png").convert("RGB")
    d = ImageDraw.Draw(im)
    for b in boxes: d.rectangle(b, outline=(220, 0, 0), width=4)
    bar = Image.new("RGB", (im.width, 38), (30, 30, 30)); ImageDraw.Draw(bar).text((10, 7), caption, fill=(255, 255, 255), font=font)
    out = Image.new("RGB", (im.width, im.height + 38)); out.paste(bar, (0, 0)); out.paste(im, (0, 38)); out.save(DST / f"run_{name}.png")
    print("annotated", name)
