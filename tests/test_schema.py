"""Structure of the extractor's JSON output, checked offline (no API call, no key needed).

1. The task's answer key must follow SCHEMA exactly: same keys, right types, nested objects and the items list.
2. The checker itself must catch a wrong type, a missing key and an unexpected key.
3. extract_order must send SCHEMA with the request (responseSchema, JSON mime type, temperature 0) and return the
   model's JSON unchanged. The HTTP call is replaced by a fake reply.
"""
import io
import json
import os
import unittest
from unittest import mock

from fakturama_bot import extract
from fakturama_bot.extract import SCHEMA

TYPES = {"STRING": str, "NUMBER": (int, float), "OBJECT": dict, "ARRAY": list}


def structure_errors(value, schema, path="$"):
    """Everything in `value` that does not follow the Gemini-style `schema` (type, nullable, properties, items)."""
    if value is None:
        return [] if schema.get("nullable") else [f"{path}: null is not allowed"]
    expected = TYPES[schema["type"]]
    if isinstance(value, bool) or not isinstance(value, expected):
        return [f"{path}: expected {schema['type']}, got {type(value).__name__}"]
    errors = []
    if schema["type"] == "OBJECT":
        props = schema.get("properties", {})
        for key in props:
            if key not in value:
                errors.append(f"{path}.{key}: missing")
        for key in value:
            if key not in props:
                errors.append(f"{path}.{key}: not in the schema")
        for key, sub in props.items():
            if key in value:
                errors += structure_errors(value[key], sub, f"{path}.{key}")
    elif schema["type"] == "ARRAY":
        for i, item in enumerate(value):
            errors += structure_errors(item, schema["items"], f"{path}[{i}]")
    return errors


def load_answer_key():
    with open("samples/task_example_order.expected.json", encoding="utf-8") as fh:
        return json.load(fh)


class SchemaStructureTests(unittest.TestCase):
    def test_answer_key_follows_the_schema(self):
        self.assertEqual(structure_errors(load_answer_key(), SCHEMA), [])

    def test_top_level_keys_are_the_ones_the_flow_uses(self):
        self.assertEqual(
            set(SCHEMA["properties"]),
            {"order_date", "external_reference", "customer_id", "currency", "debtor", "payment", "items", "totals"})

    def test_items_is_a_list_of_objects_with_the_line_fields(self):
        line = SCHEMA["properties"]["items"]["items"]["properties"]
        self.assertEqual(SCHEMA["properties"]["items"]["type"], "ARRAY")
        self.assertEqual(set(line), {"sku", "description", "unit", "quantity", "unit_net",
                                     "vat_percent", "discount_percent", "line_total"})

    def test_a_wrong_type_is_caught(self):
        data = load_answer_key()
        data["items"][0]["quantity"] = "2"        # a string where a number is required
        data["debtor"]["zip"] = 10117             # a number where a string is required
        errors = structure_errors(data, SCHEMA)
        self.assertTrue(any("items[0].quantity" in e for e in errors), errors)
        self.assertTrue(any("debtor.zip" in e for e in errors), errors)

    def test_a_missing_or_unexpected_key_is_caught(self):
        data = load_answer_key()
        del data["totals"]["gross"]
        data["comment"] = "extra"
        errors = structure_errors(data, SCHEMA)
        self.assertTrue(any("totals.gross: missing" in e for e in errors), errors)
        self.assertTrue(any("comment: not in the schema" in e for e in errors), errors)

    def test_null_is_allowed_where_the_schema_says_nullable(self):
        data = load_answer_key()
        data["debtor"]["delivery"] = None         # no separate delivery address printed
        data["debtor"]["email"] = None
        self.assertEqual(structure_errors(data, SCHEMA), [])


class ExtractorRequestTests(unittest.TestCase):
    def test_request_carries_the_schema_and_the_reply_is_returned_unchanged(self):
        answer = load_answer_key()
        reply = {"candidates": [{"content": {"parts": [{"text": json.dumps(answer)}]}}]}
        sent = {}

        def fake_urlopen(request, timeout=None):
            sent["body"] = json.loads(request.data)
            return io.BytesIO(json.dumps(reply).encode())

        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), \
                mock.patch.object(extract, "_LAST_GOOD", [None]), \
                mock.patch("urllib.request.urlopen", fake_urlopen):
            result = extract.extract_order("samples/task_example_order.png")

        config = sent["body"]["generationConfig"]
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertEqual(config["responseSchema"], SCHEMA)
        self.assertEqual(config["temperature"], 0)
        self.assertEqual(result, answer)
        self.assertEqual(structure_errors(result, SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
