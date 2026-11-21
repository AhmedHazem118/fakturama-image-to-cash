"""Try: fill the already-open 'New TAX Rate' editor as VAT 19%."""
from fakturama_bot import flow, ui
win = ui.main_window()
flow._fill_vat_editor(win, "VAT 19%", 19)
ui.screenshot("vat19_saved")
print("OK")
