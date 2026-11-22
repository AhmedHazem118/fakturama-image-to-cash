"""Probe: which e-mail endings does Fakturama keep? Edits the saved Northstar debtor's main-address e-mail,
saves, reopens and reads it back, for each candidate given on the command line."""
import sys, time
from fakturama_bot import flow, ui

TITLE = "Northstar Office GmbH, Marta Klein"
win = ui.main_window()
for cand in sys.argv[1:]:
    flow.close_tab(win, TITLE) if any(t.window_text().lstrip("*") == TITLE for t in win.descendants(control_type="TabItem")) else None
    ed = flow.open_debtor_from_list(win, TITLE)
    flow.ensure_editor_maximized(win)
    ed = flow._debtor_editor_by_title(win, TITLE) if hasattr(flow, "_debtor_editor_by_title") else ed
    flow._open_tab(ed, "Addresses"); flow._open_tab(ed, "Main address")
    box = ui.find_by_name(ed, "E-Mail", "Edit")
    ui.set_text(box, cand)
    from pywinauto.keyboard import send_keys
    send_keys("{TAB}"); time.sleep(0.6)      # explicit commit: leave the field with the keyboard
    ui.set_text(ui.find_by_name(ed, "Telephone", "Edit"), ui.read_value(ui.find_by_name(ed, "Telephone", "Edit")))  # move focus away
    flow._save_current(win, "*" + TITLE)
    time.sleep(1.5)
    flow.close_tab(win, TITLE); time.sleep(1)
    ed = flow.open_debtor_from_list(win, TITLE)
    flow.ensure_editor_maximized(win)
    flow._open_tab(ed, "Addresses"); flow._open_tab(ed, "Main address")
    print(f"typed {cand!r:40} -> after save and reopen: {ui.read_value(ui.find_by_name(ed, 'E-Mail', 'Edit'))!r}", flush=True)
