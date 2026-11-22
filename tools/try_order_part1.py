"""Try: VAT, then the Order: header, Debtor, and for each item select-or-create the product and add it.
Leaves the unsaved Order open (maximized) for the next step. Run in a clean workspace after try_debtor_full."""
import json, logging, os, subprocess, time
from fakturama_bot import flow, ui

logging.basicConfig(level=logging.INFO, format="%(message)s")
if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = subprocess.run(["powershell", "-NoProfile", "-Command", '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")'],
                                                  capture_output=True, text=True).stdout.strip()
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
win = ui.main_window()


def order_tab():
    return next(t for t in win.descendants(control_type="TabItem") if t.window_text().lstrip("*") == "New Order")


if not flow._editor_count(win):          # VAT first, only when starting a fresh order
    for pct in sorted({i["vat_percent"] for i in order["items"]}):
        print("VAT", pct, "->", flow.ensure_vat(win, f"VAT {int(pct)}%", pct))
if flow._editor_count(win):
    print("an order editor is already open: resuming with it")
    order_tab().click_input(); time.sleep(0.8)
    flow.ensure_editor_maximized(win)
else:
    print("order no.:", flow.open_new_order(win))
    flow.ensure_editor_maximized(win)
    flow.fill_header(win, order)
address_box = ui.edits_after_label(win, "Addresses", 1)[0]
if order["debtor"]["company"] in ui.read_value(address_box):
    print("debtor already selected in this order: skipping")
else:
    print("select debtor ->", flow.select_debtor(win, order["debtor"]))
added = {}
for it in order["items"]:
    sku = it["sku"]
    ok = flow.select_product(win, sku, it["unit_net"], already=added.get(sku, 0))
    if not ok:
        print(sku, "not found -> creating it")
        flow.create_product(win, it, f"VAT {int(it['vat_percent'])}%")
        order_tab().click_input(); time.sleep(1)
        flow.ensure_editor_maximized(win)
        ok = flow.select_product(win, sku, it["unit_net"], already=added.get(sku, 0))
    added[sku] = added.get(sku, 0) + 1
    print(sku, "added:", ok, "| Total Net:", flow._total_net(win))
ui.screenshot("order_with_products")
