import unittest

from toolreplay import transcript
from toolreplay.transcript import TranscriptError


class TestTranscript(unittest.TestCase):
    def test_parses_valid_lines(self):
        text = (
            '{"index": 0, "tool": "read_file", "args": {"path": "a"}, "response": {"bytes": 1}}\n'
            '{"index": 1, "tool": "list_dir", "args": {"path": "b"}, "response": {"n": 2}}\n'
        )
        records = transcript.parse_text(text)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].tool, "read_file")
        self.assertEqual(records[1].index, 1)

    def test_blank_lines_ignored(self):
        text = (
            '{"index": 0, "tool": "t", "args": {}, "response": {}}\n'
            "\n"
            '{"index": 1, "tool": "t", "args": {}, "response": {}}\n'
        )
        self.assertEqual(len(transcript.parse_text(text)), 2)

    def test_missing_field_rejected(self):
        text = '{"index": 0, "tool": "t", "args": {}}\n'
        with self.assertRaises(TranscriptError):
            transcript.parse_text(text)

    def test_unexpected_field_rejected(self):
        text = '{"index": 0, "tool": "t", "args": {}, "response": {}, "extra": 1}\n'
        with self.assertRaises(TranscriptError):
            transcript.parse_text(text)

    def test_out_of_order_index_rejected(self):
        text = (
            '{"index": 0, "tool": "t", "args": {}, "response": {}}\n'
            '{"index": 5, "tool": "t", "args": {}, "response": {}}\n'
        )
        with self.assertRaises(TranscriptError):
            transcript.parse_text(text)

    def test_bool_index_rejected(self):
        text = '{"index": true, "tool": "t", "args": {}, "response": {}}\n'
        with self.assertRaises(TranscriptError):
            transcript.parse_text(text)

    def test_canonical_call_ignores_key_order(self):
        a = transcript.parse_text(
            '{"index": 0, "tool": "t", "args": {"x": 1, "y": 2}, "response": {}}\n'
        )[0]
        b = transcript.parse_text(
            '{"index": 0, "tool": "t", "args": {"y": 2, "x": 1}, "response": {}}\n'
        )[0]
        self.assertEqual(a.canonical_call(), b.canonical_call())


if __name__ == "__main__":
    unittest.main()
