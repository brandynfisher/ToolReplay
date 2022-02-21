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
