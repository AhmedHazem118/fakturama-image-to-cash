"""Probe 6: in the Select-the-address dialog, repeat the gesture that opened a row in the main list:
double-click at x=100 (No. column), y=37 (row 1), on the dialog's table body."""
import time
from fakturama_bot import flow, ui

win = ui.main_window()
ui.find_by_name(win, "*New Order", "TabItem").click_input(); time.sleep(1)
upper, _ = ui.icons_after_label(win, "Addresses", 2)
upper.click_input()
dlg = ui.wait_until(lambda: flow._address_dialog(win), 8, what="dialog")
time.sleep(2)
body = next(p for p in dlg.descendants(control_type="Pane") if p.rectangle().width() == 774 and p.rectangle().height() > 300)
body.click_input(double=True, coords=(100, 37)); time.sleep(1.5)
print("dialog open:", flow._address_dialog(win) is not None)
box = ui.edits_after_label(win, "Addresses", 1)[0]
print("address box:", repr(ui.read_value(box)))
ui.screenshot("probe6")
