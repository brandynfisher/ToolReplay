import unittest

from toolreplay import replay, transcript
from toolreplay.findings import NON_DETERMINISM, REDUNDANT_CALL


def _records(text):
