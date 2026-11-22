import json, logging, os, subprocess
from fakturama_bot import flow, ui
logging.basicConfig(level=logging.INFO, format="%(message)s")
if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = subprocess.run(["powershell", "-NoProfile", "-Command", '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")'], capture_output=True, text=True).stdout.strip()
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
win = ui.main_window()
print("verified row:", flow.verify_saved_order(win, order, "PO000001"))
