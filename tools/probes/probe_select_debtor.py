"""Probe: in the open (unsaved) New Order, click the upper icon next to Addresses and dump the
'Select the address' dialog. Does not select or save anything."""
import time
from fakturama_bot import ui

win = ui.main_window()
ui.find_by_name(win, "*New Order", "TabItem").click_input()
time.sleep(1)
upper, lower = ui.icons_after_label(win, "Addresses", 2)
print("icons at:", upper.rectangle(), lower.rectangle())
upper.click_input()
time.sleep(2)
dlg = next((d for d in win.descendants(control_type="Window") if "Select the address" in (d.window_text() or "")), None)
print("dialog found:", dlg is not None)
if dlg:
    for d in dlg.descendants():
        r = d.rectangle()
        if r.width() <= 0:
            continue
        print(f"{d.element_info.control_type:10} | {(d.window_text() or '')[:40]!r:42} | {r.left},{r.top} {r.width()}x{r.height()}")
ui.screenshot("select_address_dialog")
