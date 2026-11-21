"""Probe: open the 'New' menu and list its entries (does not click any entry)."""
import time
from fakturama_bot import ui

win = ui.main_window()
menu = ui.find_by_name(win, "New", "MenuItem")
menu.click_input()
time.sleep(0.6)
from pywinauto import Desktop
for w in Desktop(backend="uia").windows():
    for d in w.descendants(control_type="MenuItem"):
        n = (d.window_text() or "").strip()
        if n:
            print("MenuItem |", n, "| parent window:", (w.window_text() or "")[:30])
ui.screenshot("new_menu")
