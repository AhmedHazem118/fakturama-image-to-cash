"""Probe: maximize the editor area, open New > New product, list its visible controls. Saves nothing."""
import time
from pywinauto.keyboard import send_keys
from fakturama_bot import flow, ui

win = ui.main_window()
flow.toggle_editor_maximized(win); time.sleep(1)
send_keys("{ESC}"); time.sleep(0.3)
ui.find_by_name(win, "New", "MenuItem").click_input()
ui.find_by_name(win, "New product", "MenuItem").click_input()
time.sleep(2.5)
print("tabs:", [t.window_text() for t in win.descendants(control_type="TabItem") if t.rectangle().top < 200])
for d in win.descendants():
    r = d.rectangle()
    t = d.element_info.control_type
    if r.width() <= 0 or r.left < 505 or r.top < 170 or t in ("Pane", "ScrollBar", "Thumb", "Tab", "Button", "ToolBar"):
        continue
    v = ""
    try: v = d.legacy_properties().get("Value", "")
    except Exception: pass
    print(f"{t:9} | {(d.window_text() or '')[:36]!r:38} | {r.left},{r.top} {r.width()}x{r.height()} | v={v!r}")
ui.screenshot("new_product")
