"""Read-only probe of the Order editor header: tabs open, dropdown values."""
from fakturama_bot import ui

win = ui.main_window()
items = win.descendants()
print("Editor tabs open:", [t.window_text() for t in items if t.element_info.control_type == "TabItem"])
print("Cust.Ref. boxes:", sum(1 for d in items if d.element_info.control_type == "Edit" and d.window_text() == "Cust.Ref."))
for i, d in enumerate(items):
    if d.element_info.control_type == "ComboBox":
        r = d.rectangle()
        nearby = [(x.element_info.control_type, x.window_text()) for x in items[i - 3:i + 4] if x is not d]
        print(f"ComboBox name={d.window_text()!r} id={d.element_info.automation_id} at ({r.left},{r.top}) {r.width()}x{r.height()}")
        print("   value:", repr(ui.read_value(d)), "| neighbours:", nearby)
