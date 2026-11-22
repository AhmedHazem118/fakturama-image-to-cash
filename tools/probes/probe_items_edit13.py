import time, sys
from pywinauto.uia_defines import IUIA
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
def focused():
    e = IUIA().iuia.GetFocusedElement(); r = e.CurrentBoundingRectangle
    return (e.CurrentName, e.CurrentControlType, (r.left, r.top, r.right, r.bottom))
def edits():
    return [(d.rectangle().left, d.rectangle().top, d.get_value()) for d in win.descendants(control_type="Edit")
            if g.left <= d.rectangle().left <= g.right and g.top <= d.rectangle().top <= g.bottom]
grid = flow._native_items_grid(win)
grid.click_input(coords=(112, 37)); time.sleep(0.8)          # real mouse: select the cell
print("after real click:", focused(), edits())
grid.click_input(coords=(112, 37), double=True); time.sleep(1.0)   # real double-click
print("after real dblclick:", focused(), edits())
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid13_a.png")
