"""Step 0: list the controls Fakturama exposes through UI Automation (UIA).

Read-only. Run with Fakturama open on its main screen:
    python tools/inspect_ui.py            # try the UIA backend
    python tools/inspect_ui.py win32      # try the older win32 backend
"""
import sys
from pywinauto import Desktop

backend = sys.argv[1] if len(sys.argv) > 1 else "uia"
wins = [w for w in Desktop(backend=backend).windows() if "akturama" in (w.window_text() or "")]
print(f"[{backend}] Fakturama windows found: {len(wins)}")
for w in wins:
    print("WINDOW:", repr(w.window_text()), w.element_info.control_type, w.rectangle())

if wins:
    main = wins[0]
    descendants = main.descendants()
    print(f"\nTotal controls inside the window: {len(descendants)}\n")
    kinds = {}
    for d in descendants:
        t = d.element_info.control_type
        kinds[t] = kinds.get(t, 0) + 1
    print("Controls by type:", kinds, "\n")
    print("First 80 controls with a name:")
    shown = 0
    for d in descendants:
        name = (d.window_text() or "").strip()
        if name:
            print(f"  {d.element_info.control_type:12} | {name[:60]!r} | id={d.element_info.automation_id!r}")
            shown += 1
            if shown >= 80:
                break
