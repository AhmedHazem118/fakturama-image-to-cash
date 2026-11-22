"""Try: add the items of the task example order that are not yet in the open, maximized order,
each verified by Total Net and the Items grid. Usage: python -m tools.try_select_product [SKU ...]"""
import json, logging, os, subprocess, sys
from fakturama_bot import flow, ui

logging.basicConfig(level=logging.INFO, format="%(message)s")
if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = subprocess.run(
        ["powershell", "-NoProfile", "-Command", '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")'],
        capture_output=True, text=True).stdout.strip()
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
wanted = sys.argv[1:] or [i["sku"] for i in order["items"]]
win = ui.main_window()
print("Total Net before:", flow._total_net(win))
for item in order["items"]:
    if item["sku"] in wanted:
        print(item["sku"], "->", "added" if flow.select_product(win, item["sku"], item["unit_net"]) else "NOT FOUND",
              "| Total Net:", flow._total_net(win))
ui.screenshot("products_added")
