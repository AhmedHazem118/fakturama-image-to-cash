"""Probe: dialog already open. Send mouse messages straight to the table's native window (win32 backend)
and report whether the dialog accepted a row (it closes and the order's address box fills)."""
import time
from pywinauto import Application, Desktop
from fakturama_bot import flow, ui

uwin = Desktop(backend="uia").window(title_re=r"^Fakturama - .*", control_type="Window")
pid = uwin.element_info.process_id
app = Application(backend="win32").connect(process=pid)
dlg = next(w for w in app.windows() if "Select the address" in w.window_text())
table = next(c for c in dlg.descendants() if c.class_name() == "SWT_Window0" and c.rectangle().width() == 774 and 380 < c.rectangle().height() < 420)
print("table rect:", table.rectangle())
table.click(coords=(300, 37)); time.sleep(0.7)       # single click via window messages
ui.screenshot("w32_single")
table.double_click(coords=(300, 37)); time.sleep(1.5)  # double click via window messages
still = flow._address_dialog(uwin) is not None
print("dialog open after double click:", still)
if not still:
    box = ui.edits_after_label(uwin, "Addresses", 1)[0]
    print("address box:", repr(ui.read_value(box)))
