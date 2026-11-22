"""Probe: type an e-mail into the address that carries the INVOICE role, save, reopen, read both addresses by role."""
import json, sys, time
from fakturama_bot import flow, ui

TITLE = "Northstar Office GmbH, Marta Klein"
cand = sys.argv[1]
win = ui.main_window()
def open_tabs(): return [t.window_text() for t in win.descendants(control_type="TabItem") if TITLE in t.window_text()]
if open_tabs():
    flow.close_tab(win, TITLE); time.sleep(1)
ed = flow.open_debtor_from_list(win, TITLE); flow.ensure_editor_maximized(win)
flow._open_tab(ed, "Addresses")
for tab in flow._address_tab_names(ed):
    flow._open_tab(ed, tab); time.sleep(0.4)
    if flow.read_roles(win, ed).get("Invoice addr."):
        ui.set_text(ui.find_by_name(ed, "E-Mail", "Edit"), cand)
        print("typed into the tab", repr(tab), "(Invoice role)", flush=True)
        break
flow._save_current(win, "*" + TITLE); time.sleep(1.5)
flow.close_tab(win, TITLE); time.sleep(1)
ed = flow.open_debtor_from_list(win, TITLE); flow.ensure_editor_maximized(win)
r = flow.read_debtor(win, ed)
print("invoice e-mail:", repr(r["invoice"]["email"]), "| delivery e-mail:", repr(r["delivery"]["email"]), "| tab order:", list(r["tabs"].keys()), flush=True)
print("invoice street:", r["invoice"]["street"], "| delivery street:", r["delivery"]["street"])
