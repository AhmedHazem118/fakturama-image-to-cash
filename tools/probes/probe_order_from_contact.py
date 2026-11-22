"""Probe: Debtors list -> single-click the contact row -> toolbar 'Create: New Order'.
Does the new order come with the address filled in? (Leaves a new unsaved order open.)"""
import time
from fakturama_bot import ui

win = ui.main_window()
tabs_before = [t.window_text() for t in win.descendants(control_type="TabItem") if t.rectangle().top < 200]
print("tabs before:", tabs_before)
[n for n in win.descendants(control_type="Text") if (n.window_text() or "") == "Debtors"][0].click_input(double=True)
time.sleep(2)
panes = [d for d in win.descendants(control_type="Pane") if d.rectangle().width() == 552 and d.rectangle().height() > 300]
panes[-1].click_input(coords=(100, 38))          # single click on row 1
time.sleep(0.8)
ui.screenshot("contact_row_clicked")
ui.find_by_name(win, "Create: New Order", "Button").click_input()
time.sleep(2.5)
tabs_after = [t.window_text() for t in win.descendants(control_type="TabItem") if t.rectangle().top < 200]
print("tabs after:", tabs_after)
for d in win.descendants(control_type="Edit"):
    r = d.rectangle()
    if r.width() > 0 and 320 < r.top < 400 and 560 < r.left < 700:
        print("address-ish box:", repr(ui.read_value(d)), r)
ui.screenshot("order_from_contact")
