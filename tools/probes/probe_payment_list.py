"""Probe: open the 'terms of payment' list from the navigation and dump what is readable."""
import time
from fakturama_bot import ui

win = ui.main_window()
nav = [t for t in win.descendants(control_type="Text") if (t.window_text() or "") == "terms of payment"]
print("nav entries:", len(nav))
nav[0].click_input(double=True)
time.sleep(2)
print("tabs:", [t.window_text() for t in win.descendants(control_type="TabItem")])
for d in win.descendants():
    r = d.rectangle()
    if r.width() <= 0 or r.left < 505 or r.top < 170:
        continue
    t = d.element_info.control_type
    if t in ("ScrollBar", "Thumb", "TabItem", "Tab"):
        continue
    name = (d.window_text() or "")
    if t == "Pane" and not name:
        continue
    print(f"{t:10} | {name[:50]!r:52} | top={r.top} left={r.left} | {r.width()}x{r.height()}")
ui.screenshot("terms_list")
