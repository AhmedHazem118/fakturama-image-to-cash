"""Smoke test for the helpers. Run from the project root:  python -m tools.try_helpers
Touches only an UNSAVED New Order editor (types into Cust.Ref., reads No. and Date)."""
import logging
from fakturama_bot import ui

logging.basicConfig(level=logging.INFO, format="%(message)s")

win = ui.main_window()

# Open a New Order only if no editor is open yet
if not win.child_window(title="Cust.Ref.", control_type="Edit").exists():
    ui.click(ui.find_by_name(win, "Create: New Order", "Button"))
    ui.wait_until(lambda: win.child_window(title="Cust.Ref.", control_type="Edit").exists(),
                  10, what="New Order editor to open")

no_field = ui.field_by_label(win, "No.")
date_field = ui.field_by_label(win, "Date")
print("Proposed order No. :", repr(ui.read_value(no_field)))
print("Date field shows   :", repr(ui.read_value(date_field)))

ref = ui.find_by_name(win, "Cust.Ref.", "Edit")
ui.set_text(ref, "TEST-REF-123")
print("Cust.Ref. now      :", repr(ui.read_value(ref)))

icons = ui.icons_after_label(win, "Addresses")
print("Icons beside Addresses (top to bottom):", [(i.rectangle().top, i.rectangle().left) for i in icons])
print("Screenshot:", ui.screenshot("order_header"))
