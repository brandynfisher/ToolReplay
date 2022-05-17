"""Declared tool scope parsing and overreach detection.

A scope file is JSON declaring which tools an agent is permitted to call:

    {
      "agent": "example-agent",
      "allowed_tools": ["read_file", "list_dir", "search"]
    }

Any call to a tool not in `allowed_tools` is permission overreach. Tool names
are matched exactly, case-sensitively, because a scope that quietly accepts
near-matches is not a scope.
"""

import json
from dataclasses import dataclass

from toolreplay.findings import Finding, OVERREACH
from toolreplay.transcript import Record


class ScopeError(ValueError):
    """Raised when a scope file is malformed."""


@dataclass(frozen=True)
class Scope:
    """A declared permission scope for one agent."""

    agent: str
    allowed_tools: frozenset[str]

    def permits(self, tool: str) -> bool:
        return tool in self.allowed_tools


def parse_text(text: str) -> Scope:
    """Parse scope JSON text into a Scope."""
