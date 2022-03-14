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
