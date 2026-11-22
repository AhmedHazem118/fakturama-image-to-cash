"""Probe 2: dialog is already open. Find it inside the Fakturama window tree and list its controls."""
from fakturama_bot import ui

win = ui.main_window()
items = win.descendants()
print("total descendants:", len(items))
for i, d in enumerate(items):
    if "Select the address" in (d.window_text() or ""):
        print("FOUND", d.element_info.control_type, repr(d.window_text()), "at index", i, d.rectangle())
        dlg = d
        break
else:
    dlg = None
    print("not found by title")

if dlg is not None:
    lines = []
    for d in dlg.descendants():
        lines.append(f"{d.element_info.control_type:12} | {(d.window_text() or '')[:50]!r:52} | id={d.element_info.automation_id!r} | {d.rectangle().width()}x{d.rectangle().height()}")
    open("tools/address_dialog_dump.txt", "w", encoding="utf-8").write("\n".join(lines))
    print(len(lines), "controls inside; saved tools/address_dialog_dump.txt")
    for l in lines:
        print(l)
