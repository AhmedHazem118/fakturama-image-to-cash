"""Fresh order. Which element has keyboard focus after various ways of entering the Qty cell?"""
import time
from pywinauto.uia_defines import IUIA
from PIL import ImageGrab
from fakturama_bot import flow, ui
win = ui.main_window(); flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
def focused():
    try:
        e = IUIA().iuia.GetFocusedElement()
        r = e.CurrentBoundingRectangle
        return (e.CurrentName, e.CurrentControlType, (r.left, r.top, r.right, r.bottom))
    except Exception as exc: return repr(exc)
def edits():
    return [(d.rectangle().left, d.rectangle().top, d.get_value()) for d in win.descendants(control_type="Edit")
            if g.left <= d.rectangle().left <= g.right and g.top <= d.rectangle().top <= g.bottom]
print("start focus:", focused(), edits())
grid = flow._native_items_grid(win)
grid.double_click(coords=(112, 37)); time.sleep(1.0)
print("after native dblclick:", focused(), edits())
ImageGrab.grab(bbox=(g.left, g.top, g.right, g.bottom)).save("run_output/grid12_a.png")
