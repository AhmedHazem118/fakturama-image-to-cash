"""Try: on the open (unsaved) Order set quantity and discount for every line and verify the totals against the image."""
import json, logging
from fakturama_bot import flow, ui
logging.basicConfig(level=logging.INFO, format="%(message)s")
order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
win = ui.main_window(); flow.activate_order_tab(win)
for row, it in enumerate(order["items"]):
    flow.set_line_values(win, row, it["quantity"], it["discount_percent"])
    print("line", row + 1, it["sku"], "qty", it["quantity"], "disc", it["discount_percent"], "-> Total Net", flow._total_net(win))
t = order["totals"]
print("totals verified:", flow.verify_order_totals(win, t["net"], t["vat"], t["gross"]))
ui.screenshot("order_with_lines")
