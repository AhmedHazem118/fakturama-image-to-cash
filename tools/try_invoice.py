import json, logging, os, subprocess
from fakturama_bot import flow, ui
logging.basicConfig(level=logging.INFO, format="%(message)s")
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
win = ui.main_window()
flow.open_followup_invoice(win, "PO000001")
flow.complete_invoice(win, order)
print("invoice saved as", flow.save_invoice(win))
ui.screenshot("invoice_saved")
