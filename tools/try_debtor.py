"""Try: fill the New Debtor form from the sample's expected JSON. Does not save.
The editor is expected to be maximized already (run once with arg 'max' if not)."""
import json, sys, time
from fakturama_bot import flow, ui

order = json.load(open("samples/task_example_order.expected.json", encoding="utf-8"))
win = ui.main_window()
editor = flow._debtor_editor(win)
if "max" in sys.argv:
    flow.toggle_editor_maximized(win); time.sleep(1); editor = flow._debtor_editor(win)
flow.fill_debtor(editor, order["debtor"])
ui.screenshot("debtor_filled")
print("OK: debtor form filled and read back")
