"""Save the open order once with the toolbar and report the tab titles before/after."""
import time
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
def titles(): return [t.window_text() for t in win.descendants(control_type="TabItem") if t.rectangle().top < 250]
print("before:", titles())
flow._save_current(win, "*New Order")
time.sleep(2.5)
print("after:", titles())
ui.screenshot("order_saved")
