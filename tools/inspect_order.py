"""Step 1: click 'Create: New Order' by NAME and list the order editor controls.
Saves nothing. Output goes to the console and tools/order_editor_dump.txt
"""
import time
from pywinauto import Desktop

win = Desktop(backend="uia").window(title_re=".*akturama.*")
win.set_focus()

btn = win.child_window(title="Create: New Order", control_type="Button")
print("button found:", btn.exists(timeout=3))
btn.click_input()
time.sleep(4)  # exploration only; the real code will wait for a condition

lines = []
for d in win.descendants():
    name = (d.window_text() or "").strip()
    t = d.element_info.control_type
    r = d.rectangle()
    lines.append(f"{t:12} | {name[:50]!r:52} | id={d.element_info.automation_id!r} | {r.width()}x{r.height()}")
out = "\n".join(lines)
open("tools/order_editor_dump.txt", "w", encoding="utf-8").write(out)
print(f"{len(lines)} controls total. Showing Edit/ComboBox/CheckBox/Table/Button/Text with names:\n")
for l in lines:
    if l.split("|")[0].strip() in ("Edit", "ComboBox", "CheckBox", "Table", "DataGrid", "List", "Tab", "TabItem", "Spinner"):
        print(l)
