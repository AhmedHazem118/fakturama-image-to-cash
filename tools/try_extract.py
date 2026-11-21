"""Run the extractor on the sample image and compare with the answer key.
    python -m tools.try_extract [path/to/image.png]
"""
import json
import sys
from fakturama_bot.extract import extract_order

image = sys.argv[1] if len(sys.argv) > 1 else "samples/order_sample.png"
got = extract_order(image)
print(json.dumps(got, indent=2))

try:
    expected = json.load(open("samples/order_sample.expected.json", encoding="utf-8"))
except FileNotFoundError:
    sys.exit()


def diff(a, b, path=""):
    if isinstance(b, dict):
        for k in b:
            yield from diff((a or {}).get(k), b[k], f"{path}.{k}")
    elif isinstance(b, list):
        if len(a or []) != len(b):
            yield f"{path}: expected {len(b)} rows, got {len(a or [])}"
        for i, (x, y) in enumerate(zip(a or [], b)):
            yield from diff(x, y, f"{path}[{i}]")
    elif a != b:
        yield f"{path}: expected {b!r}, got {a!r}"


problems = list(diff(got, expected))
print("\nMATCHES THE ANSWER KEY" if not problems else "\nDIFFERENCES:\n  " + "\n  ".join(problems))
