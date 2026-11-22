"""Cropped (Fakturama window only) screenshots of the finished master data: debtor tab, product tab, lists."""
import time
from pathlib import Path
from PIL import ImageGrab
from fakturama_bot import ui
OUT = Path("docs/screenshots"); OUT.mkdir(parents=True, exist_ok=True)
win = ui.main_window(); time.sleep(0.8)
def shot(name):
    r = win.rectangle()
    ImageGrab.grab(bbox=(r.left + 9, r.top, r.right - 9, r.bottom - 8)).save(OUT / f"{name}.png"); print("saved", name)
def tab(prefix):
    t = [t for t in win.descendants(control_type="TabItem") if t.window_text().lstrip("*").startswith(prefix) and t.rectangle().top < 250][0]
    t.click_input(); time.sleep(1.2)
tab("Northstar"); shot("10_debtor_saved")
tab("Ergonomic"); shot("11_product_chair")
tab("Anti-Fatigue"); shot("12_product_mat")
for i, label in enumerate(("Debtors", "Products", "VATs", "terms of payment"), start=13):
    [n for n in win.descendants(control_type="Text") if (n.window_text() or "") == label and n.rectangle().left < 400][0].click_input(double=True)
    time.sleep(2.2); shot(f"{i}_{label.replace(' ', '_')}_list")
