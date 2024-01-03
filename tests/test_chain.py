import unittest

from toolreplay import chain, transcript
from toolreplay.chain import GENESIS, Link


def _records(text):
    return transcript.parse_text(text)


SAMPLE = (
    '{"index": 0, "tool": "list_dir", "args": {"path": "docs"}, "response": {"n": 2}}\n'
    '{"index": 1, "tool": "read_file", "args": {"path": "a"}, "response": {"bytes": 1}}\n'
)


class TestChain(unittest.TestCase):
    def test_genesis_prev_is_zeroes(self):
        links = chain.seal(_records(SAMPLE))
        self.assertEqual(links[0].prev, GENESIS)

    def test_chain_links_reference_previous_digest(self):
        links = chain.seal(_records(SAMPLE))
        self.assertEqual(links[1].prev, links[0].digest)

    def test_digest_is_deterministic(self):
        a = chain.seal(_records(SAMPLE))
        b = chain.seal(_records(SAMPLE))
        self.assertEqual([l.digest for l in a], [l.digest for l in b])

    def test_verify_intact_chain(self):
        links = chain.seal(_records(SAMPLE))
        result = chain.verify(links)
        self.assertTrue(result.ok)
        self.assertIsNone(result.broken_index)

    def test_verify_detects_tampered_response(self):
        links = chain.seal(_records(SAMPLE))
        tampered = list(links)
