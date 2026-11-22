"""Probe: what are the in-cell Edit controls in the Items grid? Read only (prints text/rect/patterns)."""
from fakturama_bot import flow, ui
win = ui.main_window()
flow.activate_order_tab(win)
g = flow._items_grid_rect(win)
for d in win.descendants(control_type="Edit"):
    r = d.rectangle()
    if g.left <= r.left <= g.right and g.top <= r.top <= g.bottom:
        print("edit", r, repr(d.window_text()), repr(d.get_value() if hasattr(d, "get_value") else None), d.is_enabled(), d.is_visible())
