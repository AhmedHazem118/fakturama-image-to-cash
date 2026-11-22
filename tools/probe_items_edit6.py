import time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
send_keys("{ENTER}"); time.sleep(1.5)
print("after ENTER total", flow._total_net(win))
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid_after_enter.png")
