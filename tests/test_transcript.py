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
