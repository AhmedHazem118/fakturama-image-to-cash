import time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
eds = [d for d in win.descendants(control_type="Edit") if g.left <= d.rectangle().left <= g.right and g.top <= d.rectangle().top <= g.bottom]
e = min(eds, key=lambda d: d.rectangle().top)
print("focused edit text", e.get_value(), e.has_keyboard_focus())
e.set_focus(); send_keys("{TAB}"); time.sleep(1.2)
print("after TAB total", flow._total_net(win))
r = win.rectangle()
ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save("run_output/private_full_after_tab.png")
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid_after_tab.png")
