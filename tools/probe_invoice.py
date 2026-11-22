"""Look at the new Invoice editor: maximize, list controls near 'paid', optionally tick paid (arg 'tick')."""
import sys, time
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window()
inv = next(t for t in win.descendants(control_type="TabItem") if t.window_text().lstrip("*") == "New Invoice")
inv.click_input(); time.sleep(1.0); flow.ensure_editor_maximized(win)
paid = ui.find_by_name(win, "paid", "CheckBox")
print("paid checkbox", paid.rectangle(), "state", paid.get_toggle_state())
if len(sys.argv) > 1 and sys.argv[1] == "tick":
    paid.click_input(); time.sleep(1.0); print("now", paid.get_toggle_state())
pr = paid.rectangle()
for c in win.descendants():
    r = c.rectangle()
    if abs(r.top - pr.top) < 40 and r.width() > 0 and c.is_visible() and r.top > 300:
        print(c.element_info.control_type, repr(c.window_text()), r)
r = win.rectangle(); ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save("run_output/private_invoice2.png")
