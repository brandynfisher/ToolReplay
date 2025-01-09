import unittest

from toolreplay import replay, transcript
from toolreplay.findings import NON_DETERMINISM, REDUNDANT_CALL


def _records(text):
    return transcript.parse_text(text)


class TestReplay(unittest.TestCase):
    def test_clean_session_has_no_findings(self):
        text = (
            '{"index": 0, "tool": "list_dir", "args": {"p": "a"}, "response": {"n": 2}}\n'
