"""Does the typed Qty '2' exist in the model? Leave the order tab and come back, then read grid + totals."""
import time
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
def tab(prefix):
    t = [t for t in win.descendants(control_type="TabItem") if t.window_text().lstrip("*").startswith(prefix) and t.rectangle().top < 250][0]
    t.click_input(); time.sleep(1.2)
tab("Ergonomic"); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid11_back.png")
print("total", flow._total_net(win))
r = win.rectangle(); ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save("run_output/private_full11b.png")
