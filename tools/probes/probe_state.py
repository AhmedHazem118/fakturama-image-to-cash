"""Probe: what is open in Fakturama right now? List tabs, and named buttons/menu items."""
from fakturama_bot import ui

win = ui.main_window()
print("title:", win.window_text())
seen = set()
for d in win.descendants():
    ct = d.element_info.control_type
    name = (d.window_text() or "").strip()
    if ct in ("TabItem", "MenuItem", "Button", "TreeItem") and name and (ct, name) not in seen:
        seen.add((ct, name))
        print(f"{ct:9} | {name[:60]}")
