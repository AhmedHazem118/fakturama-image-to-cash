import time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
eds = [d for d in win.descendants(control_type="Edit") if g.left <= d.rectangle().left <= g.right and g.top <= d.rectangle().top <= g.bottom]
e = min(eds, key=lambda d: d.rectangle().top)
print("focus", e.has_keyboard_focus(), repr(e.get_value()))
if e.has_keyboard_focus():
    send_keys("^a"); send_keys("2.00"); time.sleep(0.3); send_keys("{ENTER}"); time.sleep(1.5)
print("total", flow._total_net(win))
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid10.png")
