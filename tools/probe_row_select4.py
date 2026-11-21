"""Probe 4: reopen the dialog; slow mouse (move, pause, press, release) on row 1, then double-click.
Reports whether the dialog closed on double click and what the order's address box shows."""
import time
from PIL import ImageGrab
from pywinauto import mouse
from fakturama_bot import flow, ui

win = ui.main_window()
ui.find_by_name(win, "*New Order", "TabItem").click_input(); time.sleep(1)
upper, _ = ui.icons_after_label(win, "Addresses", 2)
upper.click_input()
dlg = ui.wait_until(lambda: flow._address_dialog(win), 8, what="dialog")
time.sleep(2)
body = next(p for p in dlg.descendants(control_type="Pane") if p.rectangle().width() == 774 and p.rectangle().height() > 300)
r = body.rectangle()
x, y = r.left + 300, r.top + 37
mouse.move(coords=(x - 40, y - 15)); time.sleep(0.3)
mouse.move(coords=(x, y)); time.sleep(0.4)
mouse.press(coords=(x, y)); time.sleep(0.12); mouse.release(coords=(x, y)); time.sleep(0.8)
ImageGrab.grab(bbox=(r.left, r.top - 90, r.right + 10, r.top + 90)).save("run_output/sel_slow_click.png")
mouse.double_click(coords=(x, y)); time.sleep(1.5)
print("dialog still open after double-click:", flow._address_dialog(win) is not None)
if flow._address_dialog(win) is None:
    box = ui.edits_after_label(win, "Addresses", 1)[0]
    print("address box:", repr(ui.read_value(box)))
ui.screenshot("after_slow_dbl")
