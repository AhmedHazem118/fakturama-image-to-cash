import time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
def snap(n): ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save(f"run_output/grid9_{n}.png")
def qty_edit():
    eds = [d for d in win.descendants(control_type="Edit") if g.left <= d.rectangle().left <= g.right and g.top <= d.rectangle().top <= g.bottom]
    return min(eds, key=lambda d: d.rectangle().top)
send_keys("{ESC}"); time.sleep(0.5)
e = qty_edit()
e.click_input(double=True); time.sleep(0.8)          # real mouse double-click inside the cell
e = qty_edit(); print("focus after dblclick:", e.has_keyboard_focus(), repr(e.get_value())); snap("a")
if e.has_keyboard_focus():
    send_keys("^a"); send_keys("2"); time.sleep(0.3); snap("b")
    send_keys("{ENTER}"); time.sleep(1.5); snap("c")
    print("total", flow._total_net(win))
