"""Vision fallback: read a table that UI Automation cannot see (Fakturama's list tables are
anonymous panes). Crop the table from the screen, ask the vision model for its rows.

Used only where UIA gives no text. Every use is logged. NOTE: the crop leaves the PC (Gemini API),
so with real customer data this needs a privacy decision (see README).
"""
import hashlib
import io
import logging

from .extract import ask_gemini

log = logging.getLogger("fakturama_bot")

SCHEMA = {"type": "OBJECT", "properties": {"rows": {"type": "ARRAY", "items": {
    "type": "ARRAY", "items": {"type": "STRING"}}}}}


def read_table(rect, columns, timeout=90):
    """Return the data rows of the on-screen table inside `rect` as a list of {column: text}."""
    from PIL import ImageGrab
    shot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
    buf = io.BytesIO()
    shot.save(buf, format="PNG")
    prompt = (f"This image is a table whose columns, left to right, are: {', '.join(columns)}. "
              "Return every DATA row (not the header) as a list of cell texts in column order. "
              "Copy the text exactly as shown; use an empty string for an empty cell; "
              "a text ending in '...' is cut off by the column width, keep the dots. "
              "If there are no data rows, return an empty list.")
    rows = ask_gemini(buf.getvalue(), "image/png", prompt, SCHEMA, timeout=timeout)["rows"]
    table = [dict(zip(columns, row)) for row in rows if any(c.strip() for c in row)]
    log.info("vision read %d table row(s)", len(table))
    return table


def region_signature(rect):
    """A fingerprint of what is on screen inside `rect`; equal twice in a row = the view stopped changing."""
    from PIL import ImageGrab
    return hashlib.md5(ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).tobytes()).hexdigest()


# ------------------------------------------------ offline second reader
_PS_OCR = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Foundation, ContentType=WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, $type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(-1) | Out-Null; $t.Result }
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync('__IMG__')) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$res = Await ($eng.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
foreach ($l in $res.Lines) { $l.Text }
"""


def ocr_text(rect):
    """Offline OCR of a screen region with Windows' built-in engine (no network, no API key). Weaker than the
    vision model (confuses 0/O and 1/I, scrambles tables), so it is used only to CHECK that a known text is present."""
    import subprocess
    import tempfile
    from pathlib import Path

    from PIL import ImageGrab
    img = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "region.png"
        img.save(path)
        script = _PS_OCR.replace("__IMG__", str(path).replace("'", "''"))
        out = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=60)
    return out.stdout


def _norm(text):
    """Upper-case, letters that look like digits mapped to digits (O->0, I/L->1), non-alphanumerics dropped."""
    import re
    return re.sub(r"[^A-Z0-9]", "", text.upper().replace("O", "0").replace("I", "1").replace("L", "1"))


def count_in_ocr(rect, sku):
    """How many times `sku` appears in the OCR text of `rect` (after O/0 and I/1 normalisation)."""
    return _norm(ocr_text(rect)).count(_norm(sku))
