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

import logging

log = logging.getLogger("fakturama_bot")

# Preferred model first (reproducible results), then fallbacks that are tried when the preferred one is
# overloaded (HTTP 503/429), retired (404) or stalls (timeout). GEMINI_MODEL puts your own choice first.
DEFAULT_MODELS = ["gemini-3.8-flash", "gemini-3-flash-preview", "gemini-3.1-flash-lite"]
MODELS = ([os.environ["GEMINI_MODEL"]] if os.environ.get("GEMINI_MODEL") else []) + [
    m for m in DEFAULT_MODELS if m != os.environ.get("GEMINI_MODEL")]
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

S = {"type": "STRING", "nullable": True}
N = {"type": "NUMBER", "nullable": True}

# The JSON shape the model MUST follow. null is allowed so it never has to invent data.
SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "order_date": S,
        "external_reference": S,
        "customer_id": S,
        "currency": S,
        "debtor": {"type": "OBJECT", "properties": {
            "company": S, "first_name": S, "last_name": S, "alias": S,
            "street": S, "zip": S, "city": S, "country": S, "email": S, "phone": S,
            "delivery": {"type": "OBJECT", "nullable": True, "properties": {
                "name": S, "street": S, "zip": S, "city": S, "country": S}}}},
        "payment": {"type": "OBJECT", "properties": {"method": S, "status": S, "payment_date": S}},
        "items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
            "sku": S, "description": S, "unit": S, "quantity": N, "unit_net": N,
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
- One entry in items per table row, in the printed order. Ignore empty table rows.
- debtor.street, zip, city and country are the BILLING address. A separate DELIVERY address goes in debtor.delivery (name, street, zip, city, country); use null if none is printed.
- A single "contact name" is split into first_name (first word) and last_name (the rest).
- customer_id and currency exactly as printed (for example CUST-1007 and EUR); unit as printed (for example pcs)."""


class ExtractionError(Exception):
    pass


def ask_gemini(image_bytes, mime, prompt, schema, retries=1, timeout=45):
    """One vision call: image + prompt in, JSON (following `schema`) out. Shared by the order extractor and
    the screen-table reader (vision.py). Tries each model in MODELS in turn: an overloaded (503/429), retired
    (404) or stalled (timeout) model is skipped, and the model that answered is logged. `timeout` is per attempt."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ExtractionError("GEMINI_API_KEY is not set. See README, setup step 3.")

    data = base64.b64encode(image_bytes).decode()
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": data}}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": schema},
    }).encode()
    failures = []
    for model in MODELS:
        req = urllib.request.Request(
            BASE_URL.format(model=model), data=body,
            # key goes in a header, not the URL, so it never ends up in logs
            headers={"Content-Type": "application/json", "x-goog-api-key": key})
        for attempt in range(retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    payload = json.load(resp)
                text = payload["candidates"][0]["content"]["parts"][0]["text"]
                result = json.loads(text)
                log.info("Gemini model used: %s", model)
                return result
            except urllib.error.HTTPError as e:
                detail = e.read()[:120]
                if e.code in (429, 503) and attempt < retries:   # busy: one short wait, then retry this model
                    time.sleep(3)
                    continue
                failures.append(f"{model}: HTTP {e.code}")
                break
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                failures.append(f"{model}: unexpected reply ({e})")
                break
            except OSError as e:                                  # timeout / connection problem: next model
                failures.append(f"{model}: {type(e).__name__}")
                break
        log.warning("Gemini model %s skipped (%s)", model, failures[-1])
    raise ExtractionError("No Gemini model answered: " + "; ".join(failures))


def extract_order(image_path, retries=2):
    mime = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as fh:
        return ask_gemini(fh.read(), mime, PROMPT, SCHEMA, retries)
