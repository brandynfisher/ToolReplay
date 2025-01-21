import unittest

from toolreplay import scope, transcript
from toolreplay.findings import OVERREACH
from toolreplay.scope import ScopeError


def _records(text):
    return transcript.parse_text(text)


class TestScope(unittest.TestCase):
