"""Probe: activate the Qty cell of line 1 in the Items grid with a native double-click and see what UIA shows.
Types nothing unless an argument is given (then types it and presses Enter)."""
import sys, time
from pywinauto.keyboard import send_keys
from PIL import ImageGrab
from fakturama_bot import flow, ui

win = ui.main_window()
flow.activate_order_tab(win)
grid_rect = flow._items_grid_rect(win)
grid = flow._native_items_grid(win)
print("grid rect:", grid_rect)
def cell(col_center, row): return (col_center, 25 + 25 * row + 12)
def editors():
    return [(d.rectangle().left, d.rectangle().top, d.rectangle().width()) for d in win.descendants(control_type="Edit")
            if grid_rect.left <= d.rectangle().left <= grid_rect.right and grid_rect.top <= d.rectangle().top <= grid_rect.bottom]
print("in-cell editors before:", editors())
grid.double_click(coords=cell(112, 0)); time.sleep(0.8)
print("in-cell editors after double-click on Qty, line 1:", editors())
ImageGrab.grab(bbox=(grid_rect.left, grid_rect.top, grid_rect.right, grid_rect.bottom)).save("run_output/grid_after_dblclick.png")
if len(sys.argv) > 1:
    send_keys("^a"); send_keys(sys.argv[1]); send_keys("{ENTER}"); time.sleep(1.0)
    print("typed", sys.argv[1], "-> Total Net now", flow._total_net(win))
