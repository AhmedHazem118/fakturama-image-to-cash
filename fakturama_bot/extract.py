"""Extractor: order image -> structured dict, using a vision LLM (Gemini).

The model is only asked to READ. Checking the numbers is validate.py's job.
The API key comes from the GEMINI_API_KEY environment variable (never from code).
"""
import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request

# Pinned model name (reproducible). Override with GEMINI_MODEL if Google retires it.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

S = {"type": "STRING", "nullable": True}
N = {"type": "NUMBER", "nullable": True}

# The JSON shape the model MUST follow. null is allowed so it never has to invent data.
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "order_date": S,
        "external_reference": S,
        "debtor": {"type": "OBJECT", "properties": {
            "company": S, "first_name": S, "last_name": S, "alias": S,
            "street": S, "zip": S, "city": S, "country": S, "email": S, "phone": S}},
        "payment": {"type": "OBJECT", "properties": {"method": S, "status": S, "payment_date": S}},
        "items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "sku": S, "description": S, "quantity": N, "unit_net": N,
            "vat_percent": N, "discount_percent": N, "line_total": N}}},
        "totals": {"type": "OBJECT", "properties": {"net": N, "vat": N, "gross": N}},
    },
}

PROMPT = """Read this purchase order image and return JSON following the schema.
Rules:
- Copy text exactly as printed. Do NOT guess: if a value is not visible, use null.
- Dates as YYYY-MM-DD.
- Numbers as plain numbers with a dot decimal (1234.5), no currency symbols or % signs.
- vat_percent and discount_percent are percentages (19, not 0.19). No discount printed means 0.
- payment.method is exactly as printed (e.g. Bank Transfer). payment.status is PAID or UNPAID.
- Keep ZIP and phone numbers as strings.
- One entry in items per table row, in the printed order."""


class ExtractionError(Exception):
    pass


def ask_gemini(image_bytes, mime, prompt, schema, retries=2, timeout=90):
    """One vision call: image + prompt in, JSON (following `schema`) out. Shared by the order
    extractor and by the screen-table reader (vision.py)."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ExtractionError("GEMINI_API_KEY is not set. See README, setup step 3.")

    data = base64.b64encode(image_bytes).decode()
    body = {
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": data}}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                             "responseSchema": schema},
    }
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(),
        # key goes in a header, not the URL, so it never ends up in logs
        headers={"Content-Type": "application/json", "x-goog-api-key": key})

    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.load(resp)
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < retries:  # rate limit / busy: wait, retry
                time.sleep(5 * (attempt + 1))
                continue
            raise ExtractionError(f"Gemini returned HTTP {e.code}: {e.read()[:300]!r}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise ExtractionError(f"Unexpected model reply: {e}")


def extract_order(image_path, retries=2):
    mime = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as fh:
        return ask_gemini(fh.read(), mime, PROMPT, SCHEMA, retries)
