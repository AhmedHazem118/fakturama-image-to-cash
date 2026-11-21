"""Try: select the existing debtor in the open New Order, then dump what the order shows for the address."""
import json, os, subprocess, time
from fakturama_bot import flow, ui

if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = subprocess.run(
        ["powershell", "-NoProfile", "-Command", '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")'],
        capture_output=True, text=True).stdout.strip()
order = json.load(open("samples/order_sample.expected.json", encoding="utf-8"))
win = ui.main_window()
ui.find_by_name(win, "*New Order", "TabItem").click_input(); time.sleep(1)
print("selected:", flow.select_debtor(win, order["debtor"]))
time.sleep(1)
ui.screenshot("debtor_selected")
for d in win.descendants():
    r = d.rectangle()
    if r.width() > 0 and 250 < r.top < 460 and 505 < r.left < 1100 and d.element_info.control_type in ("Text", "Edit", "ComboBox"):
        print(f"{d.element_info.control_type:9} | {(d.window_text() or '')[:70]!r:72} | {r.left},{r.top} {r.width()}x{r.height()}")
