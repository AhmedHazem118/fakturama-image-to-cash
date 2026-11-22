import time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
grid = flow._native_items_grid(win)
grid.click(coords=(112, 37)); time.sleep(0.6)            # select the Qty cell of line 1 (native click)
send_keys("{F2}"); time.sleep(0.4)
send_keys("^a"); send_keys("2"); time.sleep(0.3)
send_keys("{ENTER}"); time.sleep(1.5)
print("total", flow._total_net(win))
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid_try7.png")
