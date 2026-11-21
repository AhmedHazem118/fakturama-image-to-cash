"""Open a New Order and fill its header from the sample order (no LLM call: uses the answer key).
    python -m tools.try_header          # opens a fresh New Order first
    python -m tools.try_header reuse    # fill the editor that is already open (for repeat tests)
Saves nothing."""
import json
import logging
import sys

from fakturama_bot import flow, ui
from fakturama_bot.validate import validate

logging.basicConfig(level=logging.INFO, format="%(message)s")
v = validate(json.load(open("samples/order_sample.expected.json", encoding="utf-8")))
assert v.ok, v.errors

win = ui.main_window()
if "reuse" not in sys.argv:
    flow.open_new_order(win)
flow.fill_header(win, v.order)
print("Screenshot:", ui.screenshot("header_filled"))
