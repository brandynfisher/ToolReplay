"""Deterministic re-execution against recorded responses.

Replay treats the transcript as its own oracle. For each call it looks up what
the same call (same tool, same arguments) returned earlier in the session. If
the recorded response for an identical call differs from what was seen before,
that is non-determinism: the environment returned two different answers to the
same question, so the session cannot be trusted to reproduce.

Replay also flags redundant calls: an identical call repeated with no
intervening call that could have changed state. Here "state change" is modelled
conservatively. Any call whose tool is listed as a mutator, or any call at all
between two identical reads, counts as a possible state change. Two identical
calls that are strictly adjacent in the transcript, or separated only by other
identical reads, are redundant.

The divergence index is the first index at which replay observes a
non-determinism, because that is where a deterministic re-execution would first
disagree with the record.
"""

from dataclasses import dataclass

from toolreplay.findings import Finding, NON_DETERMINISM, REDUNDANT_CALL
from toolreplay.transcript import Record


# Tools that change state. A call to any of these between two identical reads
# means the second read is not redundant, because the world may have moved.
DEFAULT_MUTATORS = frozenset(
    {"write_file", "delete_file", "create_file", "move_file", "run_command"}
)


@dataclass(frozen=True)
class ReplayResult:
    """Result of replaying a session."""

    findings: list[Finding]
    divergence_index: int | None
    call_count: int


def replay(records: list[Record], mutators: frozenset[str] = DEFAULT_MUTATORS) -> ReplayResult:
    """Replay records against their recorded responses.

    Returns findings for non-determinism and redundant calls, plus the first
    index where replay diverged (the first non-determinism), or None if the
    session replayed cleanly.
    """
    findings: list[Finding] = []
    divergence_index: int | None = None

    # Map canonical call -> recorded response first seen for it.
