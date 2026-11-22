"""Probe 2 (editor from probe_addresses already open): click the button beside 'address type' and list what appears.
Does not choose anything; presses ESC afterwards."""
import time
from pywinauto.keyboard import send_keys
from fakturama_bot import flow, ui

win = ui.main_window()
editor = flow._debtor_editor(win)
edit = ui.edits_after_label(editor, "address type", 1)[0]
print("address type shows:", repr(ui.read_value(edit)), edit.rectangle())
btn = next(b for b in editor.descendants(control_type="Button")
           if (b.window_text() or "") == "" and abs(b.rectangle().top - edit.rectangle().top) < 6 and b.rectangle().left >= edit.rectangle().right - 6)
print("button at", btn.rectangle())
btn.click_input(); time.sleep(1.5)
ui.screenshot("address_type_popup")
print("windows:", [w.window_text() for w in win.descendants(control_type="Window")])
for ct in ("ListItem", "MenuItem", "CheckBox", "RadioButton", "Text"):
    items = [d.window_text() for d in win.descendants(control_type=ct) if d.rectangle().width() > 0 and d.rectangle().top > 400 and d.rectangle().left > 560 and (d.window_text() or "")]
    if items and ct != "Text":
        print(ct, items[:20])
