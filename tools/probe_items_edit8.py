import time
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
grid = flow._native_items_grid(win)
grid.click(coords=(237, 62)); time.sleep(1.5)     # click the Item No. cell of line 2
print("total", flow._total_net(win))
r = win.rectangle(); ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save("run_output/private_full_try8.png")
