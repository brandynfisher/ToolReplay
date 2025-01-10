import unittest

from toolreplay import replay, transcript
from toolreplay.findings import NON_DETERMINISM, REDUNDANT_CALL


def _records(text):
    return transcript.parse_text(text)


class TestReplay(unittest.TestCase):
    def test_clean_session_has_no_findings(self):
        text = (
            '{"index": 0, "tool": "list_dir", "args": {"p": "a"}, "response": {"n": 2}}\n'
            '{"index": 1, "tool": "read_file", "args": {"p": "b"}, "response": {"b": 1}}\n'
            '{"index": 2, "tool": "search", "args": {"q": "x"}, "response": {"h": 3}}\n'
        )
        result = replay.replay(_records(text))
        self.assertEqual(result.findings, [])
        self.assertIsNone(result.divergence_index)

    def test_non_determinism_detected(self):
        text = (
            '{"index": 0, "tool": "search", "args": {"q": "x"}, "response": {"h": 3}}\n'
            '{"index": 1, "tool": "search", "args": {"q": "x"}, "response": {"h": 9}}\n'
        )
        result = replay.replay(_records(text))
        kinds = [f.kind for f in result.findings]
        self.assertIn(NON_DETERMINISM, kinds)
        self.assertEqual(result.divergence_index, 1)

    def test_redundant_call_detected(self):
        text = (
            '{"index": 0, "tool": "read_file", "args": {"p": "a"}, "response": {"b": 1}}\n'
            '{"index": 1, "tool": "read_file", "args": {"p": "a"}, "response": {"b": 1}}\n'
        )
        result = replay.replay(_records(text))
        kinds = [f.kind for f in result.findings]
        self.assertIn(REDUNDANT_CALL, kinds)
        self.assertIsNone(result.divergence_index)

    def test_mutation_between_identical_reads_is_not_redundant(self):
