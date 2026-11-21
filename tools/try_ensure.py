"""Try the existence checks (read only: nothing is created or saved)."""
from fakturama_bot import flow, ui
win = ui.main_window()
vats = flow.existing_vat_names(win)
print("VAT entries:", vats)
print("VAT 19% exists:", "VAT 19%" in vats, "| VAT 99% exists:", "VAT 99%" in vats)
pay = flow.existing_payment_names(win)
print("Payment methods:", pay)
print("Bank Transfer exists:", "Bank Transfer" in pay, "| SEPA Direct Debit exists:", "SEPA Direct Debit" in pay)
print("tabs:", [t.window_text() for t in win.descendants(control_type="TabItem") if t.rectangle().top < 200])
