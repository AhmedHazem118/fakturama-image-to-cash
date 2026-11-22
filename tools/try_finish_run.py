"""Debug aid: continue a stopped run from 'save the Order' on (the order with its lines is open and unsaved)."""
import json, logging
from fakturama_bot import flow, ui
logging.basicConfig(level=logging.INFO, format="%(message)s")
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
win = ui.main_window()
no = flow.save_order(win); flow.verify_documents(win, order, no); print("order", no, "verified")
flow.open_followup_invoice(win, no); flow.complete_invoice(win, order); inv = flow.save_invoice(win)
flow.verify_documents(win, order, no, inv); print("invoice", inv, "verified")
