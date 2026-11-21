"""Try: read the open 'Select the address' dialog table with the vision fallback. Read only."""
import os
from pywinauto import Desktop
from fakturama_bot import vision

os.environ.setdefault("GEMINI_API_KEY", "")
if not os.environ["GEMINI_API_KEY"]:
    import subprocess
    os.environ["GEMINI_API_KEY"] = subprocess.run(
        ["powershell", "-NoProfile", "-Command", '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")'],
        capture_output=True, text=True).stdout.strip()
win = Desktop(backend="uia").window(title_re=r"^Fakturama - .*", control_type="Window")
dlg = next(d for d in win.descendants(control_type="Window") if "Select the address" in (d.window_text() or ""))
body = next(p for p in dlg.descendants(control_type="Pane") if p.rectangle().width() == 774 and p.rectangle().height() > 300)
print(vision.read_table(body.rectangle(), ["No.", "First Name", "Name", "Company", "ZIP", "City"]))
