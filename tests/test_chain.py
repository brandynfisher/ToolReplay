import unittest

from toolreplay import chain, transcript
from toolreplay.chain import GENESIS, Link


def _records(text):
    return transcript.parse_text(text)


SAMPLE = (
    '{"index": 0, "tool": "list_dir", "args": {"path": "docs"}, "response": {"n": 2}}\n'
    '{"index": 1, "tool": "read_file", "args": {"path": "a"}, "response": {"bytes": 1}}\n'
)

