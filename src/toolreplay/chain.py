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
        "index": record.index,
        "tool": record.tool,
        "args": record.args,
        "response": record.response,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def seal(records: list[Record]) -> list[Link]:
    """Build the hash chain over an ordered list of records."""
    links: list[Link] = []
    prev = GENESIS
    for record in records:
        digest = _digest(prev, record)
        links.append(Link(index=record.index, prev=prev, digest=digest, record=record))
        prev = digest
    return links


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of verifying a sealed chain."""

    ok: bool
    broken_index: int | None
    expected: str | None
    found: str | None


def verify(links: list[Link]) -> VerifyResult:
    """Recompute the chain and report the first link that does not match.

    A link is valid when its stored digest equals the digest recomputed from
    its stored previous digest and record, and its previous digest equals the
    digest of the link before it.
    """
    prev = GENESIS
    for link in links:
        if link.prev != prev:
            return VerifyResult(False, link.index, prev, link.prev)
        recomputed = _digest(prev, link.record)
        if recomputed != link.digest:
            return VerifyResult(False, link.index, recomputed, link.digest)
        prev = link.digest
    return VerifyResult(True, None, None, None)


def links_to_jsonl(links: list[Link]) -> str:
