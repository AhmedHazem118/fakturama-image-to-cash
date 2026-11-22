"""Try: create the task example's Debtor (billing + delivery address with roles, alias, Net, payment method),
save it ONCE, close it, reopen it from the Debtors list and compare every field with the extracted data."""
import json, logging, time
from fakturama_bot import flow, ui

logging.basicConfig(level=logging.INFO, format="%(message)s")
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
debtor, payment = order["debtor"], order["payment"]["method"]
win = ui.main_window()
editor = flow.open_new_debtor(win)
flow.ensure_editor_maximized(win)
editor = flow._debtor_editor(win)
flow.fill_debtor(editor, debtor, payment=payment, win=win)
ui.screenshot("debtor_filled_real")
flow.save_debtor(win)
title = f"{debtor['company']}, {debtor['first_name']} {debtor['last_name']}"
print("saved; tabs:", [t.window_text() for t in win.descendants(control_type="TabItem") if t.rectangle().top < 200])
flow.close_tab(win, title); time.sleep(1)
editor = flow.open_debtor_from_list(win, title)
flow.ensure_editor_maximized(win); time.sleep(1)
read = flow.read_debtor(win, flow._debtor_editor(win))
errors, warnings = flow.check_debtor(read, debtor, payment)
print("INVOICE address:", read["invoice"])
print("DELIVERY address:", read["delivery"])
print("ERRORS:", errors or "none")
print("WARNINGS:", warnings or "none")
