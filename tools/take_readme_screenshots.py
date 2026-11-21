"""Capture cropped screenshots of the Fakturama window only (never the whole screen) into docs/screenshots/.
Leaves data untouched; opens lists and activates tabs."""
import time
from pathlib import Path
from PIL import ImageGrab
from fakturama_bot import ui

OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
win = ui.main_window()
time.sleep(0.8)


def shot(name):
    r = win.rectangle()
    ImageGrab.grab(bbox=(r.left + 9, r.top, r.right - 9, r.bottom - 8)).save(OUT / f"{name}.png")  # trim invisible border
    print("saved", name, f"{r.width()}x{r.height()}")


def open_list(label):
    [n for n in win.descendants(control_type="Text") if (n.window_text() or "") == label][0].click_input(double=True)
    time.sleep(2.2)


# 1) the Order with header + selected debtor
ui.find_by_name(win, "*New Order", "TabItem").click_input(); time.sleep(1.2)
shot("01_order_header_and_debtor")
# 2) master data lists
for i, label in enumerate(("Debtors", "VATs", "Products"), start=2):
    open_list(label)
    shot(f"0{i}_{label.lower()}_list")
