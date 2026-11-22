r"""Switch Fakturama to a new EMPTY data folder (File > Select Workspace). Fakturama restarts. Used before a clean demo run.
The folder dialog is not exposed as a normal window, so after opening it the path is typed (the dialog has the focus) and
the two buttons are pressed at the positions seen on the 1920x1080 screen of this PC - a documented exception to the
no-coordinates rule, used only for this one setup step, never during the order flow.
    python -m tools.switch_workspace D:\FaktumaData_new"""
import sys, time
from pywinauto import mouse
from pywinauto.keyboard import send_keys
from fakturama_bot import ui

path = sys.argv[1]
win = ui.main_window()
ui.find_by_name(win, "File", "MenuItem").click_input()
ui.find_by_name(win, "Select Workspace", "MenuItem").click_input()
time.sleep(3)
send_keys("^a"); send_keys(path, with_spaces=True)
time.sleep(0.5)
mouse.click(coords=(1698, 1039))     # 'Select Folder'
time.sleep(3)
mouse.click(coords=(1216, 496))      # OK on 'Fakturama will be restarted'
print("restarting on", path)
time.sleep(45)
print("title:", ui.main_window().window_text())
