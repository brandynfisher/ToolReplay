"""SHA-256 chaining and verification.

Each record is sealed into a chain link. The digest of link N is computed over
the previous digest plus the canonical bytes of record N. Changing any earlier
record changes every later digest, so tampering anywhere is detectable by
recomputing the chain and comparing.

A sealed file ends with an anchor line carrying the record count and the final
head digest. The anchor is what makes deletion and truncation detectable:
without it, an attacker can simply re-seal a shorter file. Files written by
older versions have no anchor and still verify, but verify reports them as
unanchored.

The genesis previous-digest is 64 zero hex characters.
"""

import hashlib
import json
import re
from dataclasses import dataclass

from toolreplay.transcript import Record


GENESIS = "0" * 64
SEALED_FIELDS = frozenset({"index", "prev", "digest", "tool", "args", "response"})
ANCHOR_FIELDS = frozenset({"anchor", "count", "head"})
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Link:
    """One sealed record: its index, the record, and the running digest."""

    index: int
    prev: str
    digest: str
    record: Record


@dataclass(frozen=True)
class Anchor:
    """The count and final digest written at the end of a sealed file."""

    count: int
    head: str


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
    anchored: bool = True
    anchor_error: str | None = None
    head: str | None = None


def verify(links: list[Link], anchor: Anchor | None = None) -> VerifyResult:
    """Recompute the chain and report the first link that does not match.

    A link is valid when its stored digest equals the digest recomputed from
    its stored previous digest and record, its previous digest equals the
    digest of the link before it, and its index is the expected position.

    When an anchor is supplied, the record count and final digest must match
    it too. That is what makes deletion and truncation detectable.
    """
    prev = GENESIS
    for position, link in enumerate(links):
        if link.prev != prev:
            return VerifyResult(False, link.index, prev, link.prev, anchor is not None, None, prev)
        if link.index != position:
            return VerifyResult(
                False,
                link.index,
                str(position),
                str(link.index),
                anchor is not None,
                None,
                prev,
            )
        recomputed = _digest(prev, link.record)
        if recomputed != link.digest:
            return VerifyResult(
                False, link.index, recomputed, link.digest, anchor is not None, None, prev
            )
        prev = link.digest

    if anchor is not None:
        if anchor.count != len(links):
            return VerifyResult(
                False,
                None,
                str(anchor.count),
                str(len(links)),
                True,
                "record count does not match the anchor",
                prev,
            )
        if anchor.head != prev:
            return VerifyResult(
                False,
                None,
                anchor.head,
                prev,
                True,
                "final digest does not match the anchor",
                prev,
            )
    return VerifyResult(True, None, None, None, anchor is not None, None, prev)


def links_to_jsonl(links: list[Link]) -> str:
    """Serialise sealed links to JSONL text, one link per line.

    The last line is an anchor with the record count and final digest. Output
    is deterministic: sorted keys, no incidental whitespace, trailing newline
    so the file diffs cleanly.
    """
    lines = []
    for link in links:
        obj = {
            "index": link.index,
            "prev": link.prev,
            "digest": link.digest,
            "tool": link.record.tool,
            "args": link.record.args,
            "response": link.record.response,
        }
        lines.append(
            json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        )
    head = links[-1].digest if links else GENESIS
    lines.append(
        json.dumps(
            {"anchor": True, "count": len(links), "head": head},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return "\n".join(lines) + "\n"


def _parse_line(obj: object, line_no: int):
    """Validate one JSON object and return (Link | None, Anchor | None)."""
    from toolreplay.transcript import TranscriptError

    if not isinstance(obj, dict):
        raise TranscriptError(f"line {line_no}: expected a JSON object")

    if "anchor" in obj:
        fields = set(obj)
        if fields != ANCHOR_FIELDS:
            missing = sorted(ANCHOR_FIELDS - fields)
            extra = sorted(fields - ANCHOR_FIELDS)
            raise TranscriptError(
                f"line {line_no}: invalid anchor line (missing={missing}, extra={extra})"
            )
        if obj["anchor"] is not True:
            raise TranscriptError(f"line {line_no}: anchor must be true")
        count = obj["count"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise TranscriptError(f"line {line_no}: anchor count must be a non-negative integer")
        head = obj["head"]
        if not isinstance(head, str) or not HEX64_RE.fullmatch(head):
            raise TranscriptError(f"line {line_no}: anchor head must be 64 lowercase hex characters")
        return None, Anchor(count=count, head=head)

    fields = set(obj)
    if fields != SEALED_FIELDS:
        missing = sorted(SEALED_FIELDS - fields)
        extra = sorted(fields - SEALED_FIELDS)
        raise TranscriptError(
            f"line {line_no}: invalid sealed record (missing={missing}, extra={extra})"
        )

    index = obj["index"]
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise TranscriptError(f"line {line_no}: index must be a non-negative integer")
    for field in ("prev", "digest"):
        value = obj[field]
        if not isinstance(value, str) or not HEX64_RE.fullmatch(value):
            raise TranscriptError(f"line {line_no}: {field} must be 64 lowercase hex characters")
    if not isinstance(obj["tool"], str):
        raise TranscriptError(f"line {line_no}: tool must be a string")
    if not isinstance(obj["args"], dict):
        raise TranscriptError(f"line {line_no}: args must be an object")
    if not isinstance(obj["response"], dict):
        raise TranscriptError(f"line {line_no}: response must be an object")

    record = Record(
        index=index,
        tool=obj["tool"],
        args=obj["args"],
        response=obj["response"],
    )
    return (
        Link(index=index, prev=obj["prev"], digest=obj["digest"], record=record),
        None,
    )


def load_sealed_file(path: str) -> tuple[list[Link], Anchor | None]:
    """Read a sealed JSONL file and return its links and optional anchor."""
    from toolreplay.transcript import TranscriptError

    links: list[Link] = []
    anchor: Anchor | None = None
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()

    for line_no, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        if anchor is not None:
            raise TranscriptError(f"line {line_no}: nothing may follow the anchor line")
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TranscriptError(f"line {line_no}: invalid JSON: {exc}") from exc
        link, found_anchor = _parse_line(obj, line_no)
        if link is not None:
            links.append(link)
        else:
            anchor = found_anchor
    return links, anchor


def load_sealed(path: str) -> list[Link]:
    """Read a sealed JSONL file produced by `links_to_jsonl`."""
    links, _ = load_sealed_file(path)
    return links


def verify_file(path: str) -> VerifyResult:
    """Load and verify a sealed file, including its anchor when present."""
    links, anchor = load_sealed_file(path)
    return verify(links, anchor)
