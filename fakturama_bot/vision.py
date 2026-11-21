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


def read_table(rect, columns):
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
    rows = ask_gemini(buf.getvalue(), "image/png", prompt, SCHEMA)["rows"]
    table = [dict(zip(columns, row)) for row in rows if any(c.strip() for c in row)]
    log.info("vision read %d table row(s)", len(table))
    return table


def region_signature(rect):
    """A fingerprint of what is on screen inside `rect`; equal twice in a row = the view stopped changing."""
    from PIL import ImageGrab
    return hashlib.md5(ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom)).tobytes()).hexdigest()
