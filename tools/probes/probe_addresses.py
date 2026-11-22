"""Probe (no data typed, nothing saved): New > New Debtor, maximize, dump the Addresses > Main address controls,
then open the 'address type' picker and list what it offers. Closes the picker without choosing."""
import time
from pywinauto.keyboard import send_keys
from fakturama_bot import flow, ui

win = ui.main_window()
editor = flow.open_new_debtor(win)
flow.toggle_editor_maximized(win); time.sleep(1.2)
editor = flow._debtor_editor(win)
flow._open_tab(editor, "Addresses"); time.sleep(0.8)
print("--- controls in the Addresses area (top > 380):")
for d in editor.descendants():
    r = d.rectangle(); t = d.element_info.control_type
    if r.width() <= 0 or r.top < 380 or t in ("Pane", "ScrollBar", "Thumb"):
        continue
    v = ""
    try: v = d.legacy_properties().get("Value", "")
    except Exception: pass
    print(f"{t:10} | {(d.window_text() or '')[:34]!r:36} | {r.left},{r.top} {r.width()}x{r.height()} | v={v!r}")
ui.screenshot("addresses_tab")
