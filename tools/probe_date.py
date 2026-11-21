"""Experiment 4: MM DD YYYY typed in one go, auto-advancing between segments."""
import time
from fakturama_bot import ui

win = ui.main_window()
d = ui.field_by_label(win, "Date")
h = d.rectangle().height()


def show(label):
    time.sleep(0.5)
    print(f"{label:34} -> {ui.read_value(d)!r}")


for target in ("11052026", "03122026", "12312025"):
    d.click_input(coords=(8, h // 2))
    d.type_keys(target, set_foreground=False)
    show(f"typed {target}")
d.type_keys("{TAB}", set_foreground=False); show("TAB (commit)")
