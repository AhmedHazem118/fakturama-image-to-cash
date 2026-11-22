import logging, os, subprocess
from PIL import ImageGrab
from fakturama_bot import flow, ui
if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = subprocess.run(["powershell", "-NoProfile", "-Command", '[Environment]::GetEnvironmentVariable("GEMINI_API_KEY","User")'], capture_output=True, text=True).stdout.strip()
win = ui.main_window()
for r in flow.read_documents(win): print(r)
r = win.rectangle(); ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom)).save("run_output/private_docs3.png")
