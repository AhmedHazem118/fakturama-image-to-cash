"""The .env loader: reads KEY=VALUE, never overrides a variable that is already set, ignores comments and empty values."""
import os
import tempfile
import unittest
from unittest import mock

from fakturama_bot.extract import _load_dotenv


class DotenvTest(unittest.TestCase):
    def load(self, text, env):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, ".env")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            with mock.patch.dict(os.environ, env, clear=True):
                _load_dotenv(path)
                return dict(os.environ)

    def test_reads_values_and_strips_quotes(self):
        got = self.load('# comment\nGEMINI_API_KEY="abc123"\nexport GEMINI_MODEL=m1\n', {})
        self.assertEqual(got["GEMINI_API_KEY"], "abc123")
        self.assertEqual(got["GEMINI_MODEL"], "m1")

    def test_existing_variable_wins(self):
        got = self.load("GEMINI_API_KEY=from-file\n", {"GEMINI_API_KEY": "from-environment"})
        self.assertEqual(got["GEMINI_API_KEY"], "from-environment")

    def test_empty_value_is_ignored(self):
        got = self.load("GEMINI_API_KEY=\n", {})
        self.assertNotIn("GEMINI_API_KEY", got)

    def test_missing_file_is_fine(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            _load_dotenv(os.path.join(tempfile.gettempdir(), "no-such-folder", ".env"))
            self.assertNotIn("GEMINI_API_KEY", os.environ)


if __name__ == "__main__":
    unittest.main()
