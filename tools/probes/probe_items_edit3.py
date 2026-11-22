"""Try: set row 1 Qty via its in-cell Edit, press Enter, read Total Net and the grid."""
import time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window()
flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
eds = [d for d in win.descendants(control_type="Edit") if g.left <= d.rectangle().left <= g.right and g.top <= d.rectangle().top <= g.bottom]
e = min(eds, key=lambda d: d.rectangle().top)
print("before", flow._total_net(win))
e.click_input(); time.sleep(0.3)
send_keys("^a2{ENTER}"); time.sleep(1.2)
print("after", flow._total_net(win))
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid_after_qty.png")
