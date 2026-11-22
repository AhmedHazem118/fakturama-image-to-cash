"""Probe 3 (editor open, role popup open): tick 'Invoice addr.', read both check states, close the popup, read the
address type box; then click '+' and list the tabs and the new address's controls. Nothing is saved."""
import time
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from fakturama_bot import ui

win = Desktop(backend="uia").window(title_re=r"^Fakturama - .*", control_type="Window")


def boxes():
    return {c.window_text(): c for c in win.descendants(control_type="CheckBox") if (c.window_text() or "") in ("Invoice addr.", "Delivery addr.")}


b = boxes()
print("popup open:", sorted(b))
print("states before:", {k: v.get_toggle_state() for k, v in b.items()})
b["Invoice addr."].click_input(); time.sleep(0.6)
b = boxes()
print("states after clicking Invoice:", {k: v.get_toggle_state() for k, v in b.items()} if b else "popup closed")
ui.screenshot("roles_invoice_ticked")
send_keys("{ESC}"); time.sleep(0.6)
editor = next(p for p in win.descendants(control_type="Pane") if p.window_text() == "New Debtor")
edit = ui.edits_after_label(editor, "address type", 1)[0]
print("address type box now shows:", repr(ui.read_value(edit)))
print("tabs:", [t.window_text() for t in editor.descendants(control_type="TabItem")])
plus = next(x for x in editor.descendants(control_type="Button") if x.window_text() == "+")
plus.click_input(); time.sleep(1.5)
print("tabs after +:", [t.window_text() for t in editor.descendants(control_type="TabItem")])
ui.screenshot("second_address")
streets = [e for e in editor.descendants(control_type="Edit") if e.window_text() == "Street"]
print("Street edits:", [(e.rectangle().left, e.rectangle().top, e.rectangle().width()) for e in streets])
