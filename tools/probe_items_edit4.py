import time
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
print("total now", flow._total_net(win))
grid = flow._native_items_grid(win)
grid.click(coords=(500, 62)); time.sleep(1.2)     # click an empty row area / other cell
print("after clicking elsewhere", flow._total_net(win))
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid_after_qty2.png")
