"""One command for the whole flow: order image -> JSON -> validation -> Fakturama (master data, Order, Invoice),
with a verification after every stage and a run report.

    python -m fakturama_bot.run samples/task_example_order.png
    python -m fakturama_bot.run --json samples/task_example_order.expected.json     (skip the AI reading)

Fakturama must be open on an EMPTY data folder (a second run on the same folder would find the first run's
documents and stop at the final check). Any doubt stops the run with a screenshot; nothing is guessed."""
import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from . import flow, ui
from .validate import validate

log = logging.getLogger("run")


class Report:
    def __init__(self):
        self.steps = []

    def add(self, name, result, detail=""):
        self.steps.append({"step": name, "result": result, "detail": detail})
        print(f"[{result:>7}] {name}" + (f" - {detail}" if detail else ""), flush=True)

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "steps": self.steps}, indent=2), encoding="utf-8")


def _create_debtor(win, debtor, payment):
    editor = flow.open_new_debtor(win)
    flow.ensure_editor_maximized(win)
    editor = flow._debtor_editor(win)
    flow.fill_debtor(editor, debtor, payment=payment, win=win)
    flow.save_debtor(win)
    title = f"{debtor['company']}, {debtor['first_name']} {debtor['last_name']}"
    flow.close_tab(win, title)
    time.sleep(1)
    flow.open_debtor_from_list(win, title)
    flow.ensure_editor_maximized(win)
    time.sleep(1)
    read = flow.read_debtor(win, flow._debtor_editor(win))
    errors, warnings = flow.check_debtor(read, debtor, payment)
    flow.close_tab(win, title)
    if errors:
        ui.fail("Saved debtor differs from the image: " + "; ".join(errors))
    return warnings


def run(order, report):
    win = ui.main_window()
    payment = order["payment"]["method"]

    for pct in sorted({i["vat_percent"] for i in order["items"]}):
        report.add(f"VAT {int(pct)}%", flow.ensure_vat(win, f"VAT {int(pct)}%", pct))
    report.add(f"Payment method {payment}", flow.ensure_payment_term(win, payment))

    number = flow.open_new_order(win)
    flow.ensure_editor_maximized(win)
    flow.fill_header(win, order)
    report.add("Order header", "ok", f"{number}, {order['order_date']}, {order['external_reference']}, Net")

    if flow.select_debtor(win, order["debtor"]):
        report.add("Debtor", "reused")
    else:
        warnings = _create_debtor(win, order["debtor"], payment)
        report.add("Debtor created, saved, reopened and compared", "created", "; ".join(warnings))
        flow.activate_order_tab(win)
        if not flow.select_debtor(win, order["debtor"]):
            ui.fail("The new debtor could not be selected in the order")
        report.add("Debtor", "selected")

    flow.activate_order_tab(win)
    added = {}
    for item in order["items"]:
        sku = item["sku"]
        if flow.select_product(win, sku, item["unit_net"], already=added.get(sku, 0)):
            how = "reused"
        else:
            flow.create_product(win, item, f"VAT {int(item['vat_percent'])}%")
            flow.activate_order_tab(win)
            if not flow.select_product(win, sku, item["unit_net"], already=added.get(sku, 0)):
                ui.fail(f"Product {sku} was created but could not be added to the order")
            how = "created"
        added[sku] = added.get(sku, 0) + 1
        report.add(f"Product {sku}", how, f"Total Net {flow._total_net(win)}")

    for row, item in enumerate(order["items"]):
        flow.set_line_values(win, row, item["quantity"], item["discount_percent"])
    t = order["totals"]
    got = flow.verify_order_totals(win, t["net"], t["vat"], t["gross"])
    report.add("Quantities, discounts and totals", "ok", f"net {got['net']}, VAT {got['vat']}, gross {got['gross']}")

    order_no = flow.save_order(win)
    flow.verify_documents(win, order, order_no)
    report.add("Order saved and found in Data > Documents", "ok", f"{order_no}, state open, total {t['gross']}")

    flow.open_followup_invoice(win, order_no)
    flow.complete_invoice(win, order)
    inv_no = flow.save_invoice(win)
    flow.verify_documents(win, order, order_no, inv_no)
    report.add("Invoice saved and found in Data > Documents", "ok", f"{inv_no} paid, {order_no} still open")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", nargs="?", help="order image (PNG/JPG)")
    ap.add_argument("--json", help="use this already-extracted order JSON instead of reading an image")
    ap.add_argument("--report", default="run_output/run_report.json")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    report = Report()
    try:
        if args.json:
            raw = json.loads(Path(args.json).read_text(encoding="utf-8"))
            report.add("Read order", "skipped", f"using {args.json}")
        elif args.image:
            from .extract import extract_order
            raw = extract_order(args.image)
            report.add("Read order image", "ok", args.image)
        else:
            ap.error("give an image or --json")
        checked = validate(raw)
        if checked.errors:
            report.add("Validation", "STOP", "; ".join(checked.errors))
            report.save(args.report)
            return 2
        report.add("Validation", "ok", "arithmetic, dates and payment rules")
        run(checked.order, report)
    except ui.UIError as exc:
        report.add("STOPPED", "STOP", str(exc))
        report.save(args.report)
        return 1
    report.save(args.report)
    print("Run finished. Report:", args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
