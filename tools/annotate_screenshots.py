"""Add a caption banner and red boxes to the cropped screenshots (originals stay in docs/screenshots, results go to docs/annotated)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
SRC, DST = Path("docs/screenshots"), Path("docs/annotated"); DST.mkdir(exist_ok=True)
ITEMS = {
 "10_debtor_saved": ("Debtor created by the bot from the image, saved and read back: alias, net pricing, payment method 'Bank Transfer'",
                     [(460, 478, 843, 506), (990, 512, 1440, 540)]),
 "11_product_chair": ("Product CHR-ERG-01 created by the bot (gross price = net x (1 + VAT/100), cost 0, stock 0)", []),
 "12_product_mat": ("Product MAT-DESK-02: net 40.00 + 19% VAT -> gross 47.60, VAT 19% selected, cost 0, stock 0",
                    [(463, 448, 597, 474), (444, 510, 548, 537)]),
 "14_Products_list": ("Products list after the run: both SKUs from the order image exist exactly once", [(902, 235, 1455, 285)]),
 "13_Debtors_list": ("Debtors list: one debtor for the customer on the order image", []),
 "15_VATs_list": ("VAT rates available (19% created/reused by check-before-create)", []),
 "16_terms_of_payment_list": ("Payment methods: 'Bank Transfer' exists (created once, reused afterwards)", []),
}
font = ImageFont.truetype("arial.ttf", 20)
for name, (caption, boxes) in ITEMS.items():
    im = Image.open(SRC / f"{name}.png").convert("RGB")
    d = ImageDraw.Draw(im)
    for b in boxes: d.rectangle(b, outline=(220, 0, 0), width=4)
    bar = Image.new("RGB", (im.width, 38), (30, 30, 30)); ImageDraw.Draw(bar).text((10, 7), caption, fill=(255, 255, 255), font=font)
    out = Image.new("RGB", (im.width, im.height + 38)); out.paste(bar, (0, 0)); out.paste(im, (0, 38)); out.save(DST / f"{name}.png")
    print("annotated", name)
