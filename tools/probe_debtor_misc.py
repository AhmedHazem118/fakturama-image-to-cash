"""Probe: click the Miscellaneous tab of the open New Debtor editor and list its controls (no saving)."""
import time
from fakturama_bot import ui

win = ui.main_window()
tabs = [t for t in win.descendants(control_type="TabItem") if t.window_text() == "Miscellaneous"]
print("Miscellaneous tabs:", len(tabs))
tabs[0].click_input()
time.sleep(1.0)
for d in win.descendants():
    r = d.rectangle()
    if r.width() <= 0 or not (370 < r.top < 590) or r.left < 512 or d.element_info.control_type in ("Pane", "ScrollBar", "Thumb"):
        continue
    v = ""
    try:
        v = d.legacy_properties().get("Value", "")
    except Exception:
        pass
    print(f"{d.element_info.control_type:10} | {(d.window_text() or '')[:40]!r:42} | top={r.top} left={r.left} | {r.width()}x{r.height()} | v={v!r}")
ui.screenshot("debtor_misc")
