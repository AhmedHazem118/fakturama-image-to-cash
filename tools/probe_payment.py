"""Probe: open New > New Term of Payment and list its visible controls (nothing is saved)."""
import time
from pywinauto.keyboard import send_keys
from fakturama_bot import ui

win = ui.main_window()
send_keys("{ESC}"); time.sleep(0.3)
ui.find_by_name(win, "New", "MenuItem").click_input()
ui.find_by_name(win, "New Term of Payment", "MenuItem").click_input()
time.sleep(2)
print("tabs:", [t.window_text() for t in win.descendants(control_type="TabItem")])
for d in win.descendants():
    r = d.rectangle()
    if r.width() <= 0 or r.left < 505 or r.top < 170 or d.element_info.control_type in ("Pane", "ScrollBar", "Thumb"):
        continue
    if d.element_info.control_type in ("TabItem", "Tab") :
        continue
    v = ""
    try: v = d.legacy_properties().get("Value", "")
    except Exception: pass
    print(f"{d.element_info.control_type:10} | {(d.window_text() or '')[:40]!r:42} | top={r.top} left={r.left} | {r.width()}x{r.height()} | v={v!r}")
ui.screenshot("new_term_of_payment")
