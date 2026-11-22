"""Experiment: how can we read and change the price-mode dropdown (Gross/Net)?"""
import time
from fakturama_bot import ui

win = ui.main_window()
date_field = ui.field_by_label(win, "Date")
items = win.descendants()
combo = next(c for c in items if c.element_info.control_type == "ComboBox" and c.rectangle().top == date_field.rectangle().top - 5
             or (c.element_info.control_type == "ComboBox" and abs(c.rectangle().top - date_field.rectangle().top) < 15))
print("combo rect:", combo.rectangle())


def readings(c):
    out = {}
    for name in ("get_value", "selected_text", "window_text", "texts"):
        try:
            out[name] = getattr(c, name)()
        except Exception as e:
            out[name] = f"ERR {type(e).__name__}"
    out["children"] = [(x.element_info.control_type, x.window_text()) for x in c.children()]
    return out


print("before:", readings(combo))
try:
    combo.select("Net")
    time.sleep(0.8)
    print("after select('Net'):", combo.selected_text())
except Exception as e:
    print("select ERR", type(e).__name__, str(e)[:120])
    combo.click_input()
    combo.type_keys("{DOWN}{ENTER}", set_foreground=False)
    time.sleep(0.8)
    print("after keyboard:", combo.selected_text())
try:
    print("item texts:", combo.item_texts())
except Exception as e:
    print("item_texts ERR", type(e).__name__, e)
