"""Probe: open 'Select the address' with UIA, then inspect the same dialog through the win32 backend
(native window classes). Read-only; leaves the dialog open."""
import time
from pywinauto import Application, Desktop
from fakturama_bot import flow, ui

win = ui.main_window()
ui.find_by_name(win, "*New Order", "TabItem").click_input(); time.sleep(1)
upper, _ = ui.icons_after_label(win, "Addresses", 2)
upper.click_input()
ui.wait_until(lambda: flow._address_dialog(win), 8, what="dialog"); time.sleep(1.5)

pid = win.element_info.process_id
app = Application(backend="win32").connect(process=pid)
for w in app.windows():
    t = w.window_text()
    print(f"TOP {w.class_name():28} | {t[:50]!r} | {w.rectangle()}")
    if "Select the address" in t:
        for c in w.descendants():
            print(f"   {c.class_name():28} | {c.window_text()[:40]!r} | {c.rectangle()} | vis={c.is_visible()}")
