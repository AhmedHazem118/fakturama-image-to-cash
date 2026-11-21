"""Try: close the terms list, create 'Bank Transfer'."""
from fakturama_bot import flow, ui
win = ui.main_window()
flow.close_tab(win, "terms of payment")
flow.create_payment_term(win, "Bank Transfer")
ui.screenshot("payment_created")
print("OK")
