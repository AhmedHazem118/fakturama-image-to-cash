import time
from pywinauto.keyboard import send_keys
from pywinauto.uia_defines import IUIA
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
grid = flow._native_items_grid(win)
def focused_rect():
    r = IUIA().iuia.GetFocusedElement().CurrentBoundingRectangle; return (r.left, r.top, r.right, r.bottom)
grid.click_input(coords=(112, 37)); time.sleep(0.8)
print("focus", focused_rect())
send_keys("2"); time.sleep(0.4)
send_keys("{ENTER}"); time.sleep(1.5)
print("total", flow._total_net(win), "focus", focused_rect())
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid14.png")
