"""Try: clear the order's address box, run select_debtor, then confirm the box shows the debtor."""
import json, os, subprocess, time
from pywinauto.keyboard import send_keys
from fakturama_bot import flow, ui

if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = subprocess.run(
        ["powershell", "-NoProfile", "-Command", '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")'],
        capture_output=True, text=True).stdout.strip()
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
win = ui.main_window()
ui.find_by_name(win, "*New Order", "TabItem").click_input(); time.sleep(1)
box = ui.edits_after_label(win, "Addresses", 1)[0]
box.click_input(); send_keys("^a{BACKSPACE}"); time.sleep(0.5)
print("box cleared, now:", repr(ui.read_value(box)))
print("selected:", flow.select_debtor(win, order["debtor"]))
print("box:", repr(ui.read_value(ui.edits_after_label(win, "Addresses", 1)[0])))
