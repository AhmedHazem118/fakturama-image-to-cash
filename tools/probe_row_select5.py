"""Probe 5 (dialog already open): keyboard only from the search box: DOWN, then ENTER. Report outcome."""
import time
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from fakturama_bot import ui

win = Desktop(backend="uia").window(title_re=r"^Fakturama - .*", control_type="Window")
def dlg():
    return next((d for d in win.descendants(control_type="Window") if "Select the address" in (d.window_text() or "")), None)
d = dlg()
search = next(e for e in d.descendants(control_type="Edit") if e.rectangle().width() == 150)
search.click_input(); time.sleep(0.3)
send_keys("{DOWN}"); time.sleep(0.5)
send_keys("{ENTER}"); time.sleep(1.5)
print("dialog open after DOWN+ENTER:", dlg() is not None)
if dlg() is None:
    box = ui.edits_after_label(win, "Addresses", 1)[0]
    print("address box:", repr(ui.read_value(box)))
ui.screenshot("after_down_enter")
