"""Probe (nothing saved): New > New Term of Payment, list the payment-code dropdown entries and the zero fields."""
import time
from pywinauto.keyboard import send_keys
from fakturama_bot import flow, ui

win = ui.main_window()
send_keys("{ESC}"); time.sleep(0.3)
ui.click(ui.find_by_name(win, "New", "MenuItem"))
ui.click(ui.find_by_name(win, "New Term of Payment", "MenuItem"))
spec = win.child_window(title="New Term of Payment", control_type="Pane")
ui.wait_until(spec.exists, 10, what="New Term of Payment editor")
ed = spec.wrapper_object()
flow.toggle_editor_maximized(win); time.sleep(1.0)
code = ui.field_by_label(ed, "!editorPaymentPaymentcode!", ("ComboBox",))
print("current code:", repr(code.selected_text()))
code.expand(); time.sleep(0.5)
items = [d.window_text() for d in code.descendants(control_type="ListItem")]
code.collapse()
print("payment codes offered:", items)
for lab in ("Cash discount", "Discount Days", "Net Days"):
    print(lab, "=", repr(ui.read_value(ui.find_by_name(ed, lab, "Edit"))))
