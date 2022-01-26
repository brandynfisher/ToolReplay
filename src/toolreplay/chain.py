"""SHA-256 chaining and verification.

Each record is sealed into a chain link. The digest of link N is computed over
the previous digest plus the canonical bytes of record N. Changing any earlier
record changes every later digest, so tampering anywhere is detectable by
recomputing the chain and comparing.

The genesis previous-digest is 64 zero hex characters.
"""

import hashlib
import json
from dataclasses import dataclass

from toolreplay.transcript import Record


GENESIS = "0" * 64


@dataclass(frozen=True)
class Link:
    """One sealed record: its index, the record, and the running digest."""

    index: int
    prev: str
    digest: str
    record: Record


def _digest(prev: str, record: Record) -> str:
    payload = {
        "prev": prev,
