"""JSONL session records.

A session transcript is a JSON Lines file. Each line is one tool invocation
with these fields:

    index    integer, monotonically increasing from 0
    tool     string, the tool name that was called
    args     object, the arguments passed to the tool
    response object, the recorded response the tool returned

Blank lines are ignored. Parsing is strict: an unknown field, a missing
required field, or an out-of-order index is a hard error, because an audit
tool that silently repairs its input cannot be trusted.
"""

import json
from dataclasses import dataclass


REQUIRED_FIELDS = ("index", "tool", "args", "response")


class TranscriptError(ValueError):
    """Raised when a transcript line cannot be parsed or is inconsistent."""


@dataclass(frozen=True)
class Record:
    """One recorded tool invocation."""

    index: int
    tool: str
    args: dict
    response: dict

    def canonical_call(self) -> str:
        """Return a stable string identifying the call (tool plus args).

        Two calls with the same tool name and the same arguments produce the
        same canonical string, regardless of key ordering in the source JSON.
        """
        return json.dumps(
            {"tool": self.tool, "args": self.args},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def canonical_response(self) -> str:
        """Return a stable string for the recorded response."""
        return json.dumps(
            self.response,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )


def _parse_line(raw: str, line_no: int) -> Record:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TranscriptError(f"line {line_no}: invalid JSON: {exc}") from exc

    if not isinstance(obj, dict):
        raise TranscriptError(f"line {line_no}: expected a JSON object")

    for field in REQUIRED_FIELDS:
        if field not in obj:
            raise TranscriptError(f"line {line_no}: missing field {field!r}")

    extra = set(obj) - set(REQUIRED_FIELDS)
    if extra:
        names = ", ".join(sorted(extra))
        raise TranscriptError(f"line {line_no}: unexpected field(s): {names}")

    if not isinstance(obj["index"], int) or isinstance(obj["index"], bool):
        raise TranscriptError(f"line {line_no}: index must be an integer")
    if not isinstance(obj["tool"], str):
        raise TranscriptError(f"line {line_no}: tool must be a string")
    if not isinstance(obj["args"], dict):
        raise TranscriptError(f"line {line_no}: args must be an object")
    if not isinstance(obj["response"], dict):
        raise TranscriptError(f"line {line_no}: response must be an object")

    return Record(
        index=obj["index"],
        tool=obj["tool"],
        args=obj["args"],
        response=obj["response"],
    )


def parse_text(text: str) -> list[Record]:
    """Parse transcript text into an ordered list of records.

    Indices must start at 0 and increase by exactly 1 with no gaps.
    """
    records: list[Record] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        records.append(_parse_line(raw, line_no))

    for expected, record in enumerate(records):
        if record.index != expected:
            raise TranscriptError(
                f"index out of order: expected {expected}, got {record.index}"
            )
    return records


def load(path: str) -> list[Record]:
    """Read and parse a transcript file from disk."""
    with open(path, "r", encoding="utf-8") as handle:
