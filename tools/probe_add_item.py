"""Probe: close the blank extra order tab, activate the real order, click the upper icon next to Items and dump
the dialog that opens. Selects nothing."""
import time
from fakturama_bot import flow, ui

win = ui.main_window()
tabs = [t.window_text() for t in win.descendants(control_type="TabItem") if t.rectangle().top < 200]
print("tabs:", tabs)
if "New Order" in tabs:
    flow.close_tab(win, "New Order")            # the blank, never-edited order: no save prompt
    time.sleep(1)
ui.find_by_name(win, "*New Order", "TabItem").click_input(); time.sleep(1)
flow.toggle_editor_maximized(win); time.sleep(1.2)
icons = ui.icons_after_label(win, "Items", 4)
for i, ic in enumerate(icons):
    print("icon", i, ic.element_info.control_type, ic.rectangle())
before = {id(w) for w in win.descendants(control_type="Window")}
icons[0].click_input()
time.sleep(2.5)
wins = [d for d in win.descendants(control_type="Window")]
print("windows now:", [w.window_text() for w in wins])
for w in wins:
    for d in w.descendants():
        r = d.rectangle()
        if r.width() <= 0:
            continue
        print(f"{d.element_info.control_type:10} | {(d.window_text() or '')[:40]!r:42} | {r.left},{r.top} {r.width()}x{r.height()}")
ui.screenshot("add_item_dialog")
