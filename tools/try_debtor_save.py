"""Try: re-activate the debtor tab, fill with payment, save."""
import json
from fakturama_bot import flow, ui
order = json.load(open("samples/order_sample.expected.json", encoding="utf-8"))
win = ui.main_window()
ui.click(ui.find_by_name(win, "*New Debtor", "TabItem"))
editor = flow._debtor_editor(win)
flow.fill_debtor(editor, order["debtor"], payment="Bank Transfer")
ui.screenshot("debtor_before_save")
flow.save_debtor(win)
ui.screenshot("debtor_saved")
print("OK saved")
