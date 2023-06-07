"""Finding types shared across the analysis modules.

A Finding is a single audit result. Findings sort deterministically by
(index, kind) so report output is byte-identical for identical input.
"""

from dataclasses import dataclass
from functools import total_ordering


NON_DETERMINISM = "non-determinism"
REDUNDANT_CALL = "redundant-call"
OVERREACH = "permission-overreach"

KIND_ORDER = {NON_DETERMINISM: 0, REDUNDANT_CALL: 1, OVERREACH: 2}


@total_ordering
@dataclass(frozen=True)
class Finding:
    """One audit result tied to a call index."""

    kind: str
    index: int
    detail: str

    def _key(self):
        return (self.index, KIND_ORDER.get(self.kind, 99), self.detail)

    def __lt__(self, other):
        if not isinstance(other, Finding):
            return NotImplemented
        return self._key() < other._key()

    def line(self) -> str:
        """One-line rendering for report output."""
        return f"index {self.index}: {self.kind}: {self.detail}"


def sort_findings(findings: list[Finding]) -> list[Finding]:
    """Return findings in deterministic order."""
    return sorted(findings)
