"""Try: fill the already-open 'New product' editor with the first sample item (KB-100)."""
import json
from fakturama_bot import flow, ui
order = json.load(open("samples/order_sample.expected.json", encoding="utf-8"))
item = order["items"][0]
win = ui.main_window()
flow._fill_product_editor(win, item, "VAT 19%")
ui.screenshot("product1_saved")
print("OK", item["sku"])
