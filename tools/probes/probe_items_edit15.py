import time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
grid = flow._native_items_grid(win)
grid.click_input(coords=(112, 62)); time.sleep(0.6); send_keys("3{ENTER}"); time.sleep(1.2)
print("after qty2=3:", flow._total_net(win))
grid.click_input(coords=(990, 37)); time.sleep(0.6); send_keys("10{ENTER}"); time.sleep(1.5)
print("after disc1=10:", flow._total_net(win))
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid15.png")
r = win.rectangle(); ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save("run_output/private_full15.png")
