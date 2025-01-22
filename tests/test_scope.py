import unittest

from toolreplay import scope, transcript
from toolreplay.findings import OVERREACH
from toolreplay.scope import ScopeError


def _records(text):
    return transcript.parse_text(text)


class TestScope(unittest.TestCase):
    def test_parse_scope(self):
        s = scope.parse_text('{"agent": "a", "allowed_tools": ["read_file", "search"]}')
        self.assertEqual(s.agent, "a")
        self.assertTrue(s.permits("read_file"))
        self.assertFalse(s.permits("write_file"))

    def test_invalid_scope_rejected(self):
        with self.assertRaises(ScopeError):
            scope.parse_text('{"agent": "a"}')
        with self.assertRaises(ScopeError):
            scope.parse_text('{"allowed_tools": []}')
        with self.assertRaises(ScopeError):
            scope.parse_text("not json")

    def test_exact_case_sensitive_match(self):
        s = scope.parse_text('{"agent": "a", "allowed_tools": ["read_file"]}')
        self.assertFalse(s.permits("Read_File"))

    def test_detect_overreach(self):
        s = scope.parse_text('{"agent": "a", "allowed_tools": ["read_file"]}')
