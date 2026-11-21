"""Cropped screenshot (Fakturama window only) of the open order with its item lines -> docs/screenshots/05_order_with_items.png.
The order editor should be maximized and showing the Items grid."""
import time
from pathlib import Path
from PIL import ImageGrab
from fakturama_bot import ui

win = ui.main_window()
ui.find_by_name(win, "*New Order", "TabItem").click_input()
time.sleep(1.0)
r = win.rectangle()
out = Path("docs/screenshots/05_order_with_items.png")
ImageGrab.grab(bbox=(r.left + 9, r.top, r.right - 9, r.bottom - 8)).save(out)  # trim invisible border
print("saved", out)
