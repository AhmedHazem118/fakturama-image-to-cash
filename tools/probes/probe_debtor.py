"""Probe: open New > New Debtor, dump every control of the new editor to tools/debtor_editor_dump.txt (nothing is saved)."""
import time
from fakturama_bot import ui

win = ui.main_window()
from pywinauto.keyboard import send_keys
send_keys("{ESC}{ESC}"); time.sleep(0.4)
before = {d.window_text() for d in win.descendants(control_type="TabItem")}
ui.find_by_name(win, "New", "MenuItem").click_input()
time.sleep(0.5)
ui.find_by_name(win, "New Debtor", "MenuItem").click_input()
time.sleep(2.0)
after = [d.window_text() for d in win.descendants(control_type="TabItem")]
print("tabs now:", after)
lines = []
for d in win.descendants():
    r = d.rectangle()
    if r.width() <= 0:
        continue
    lines.append(f"{d.element_info.control_type:10} | {(d.window_text() or '')[:45]!r:47} | top={r.top} left={r.left} | {r.width()}x{r.height()} | v={ (d.legacy_properties().get('Value','') if hasattr(d,'legacy_properties') else '')!r}"[:200])
open("tools/debtor_editor_dump.txt", "w", encoding="utf-8").write("\n".join(lines))
print(len(lines), "visible controls saved")
ui.screenshot("new_debtor")
