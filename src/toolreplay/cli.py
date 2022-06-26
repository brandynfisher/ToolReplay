"""argparse CLI with subcommands.

Subcommands:
    seal      read a transcript, print the hash-chained sealed JSONL
    replay    replay a transcript, report non-determinism and redundant calls
    verify    verify a sealed JSONL chain is intact
    scope     check a transcript against a declared scope file
    version   print the version

Exit codes: 0 clean, 1 findings present or chain broken, 2 usage error.
"""

import argparse
import sys

from toolreplay import __version__
from toolreplay import chain, replay, report, scope, transcript
from toolreplay.transcript import TranscriptError
from toolreplay.scope import ScopeError
