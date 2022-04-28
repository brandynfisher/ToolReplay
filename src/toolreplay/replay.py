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
    seen_response: dict[str, str] = {}
    # Map canonical call -> index it was last observed at.
    last_seen_index: dict[str, int] = {}

    for pos, record in enumerate(records):
        call = record.canonical_call()
        response = record.canonical_response()

        if call in seen_response:
            if seen_response[call] != response:
                findings.append(
                    Finding(
                        kind=NON_DETERMINISM,
                        index=record.index,
                        detail=(
                            f"tool {record.tool!r} returned a different response "
                            f"than the identical call at index "
                            f"{last_seen_index[call]}"
                        ),
                    )
                )
                if divergence_index is None:
                    divergence_index = record.index
            else:
                # Identical response. Redundant if nothing between the two
                # identical calls could have changed state.
                prev_pos = None
                for back in range(pos - 1, -1, -1):
                    if records[back].canonical_call() == call:
                        prev_pos = back
                        break
                if prev_pos is not None and _no_state_change_between(
                    records, prev_pos, pos, call, mutators
                ):
                    findings.append(
                        Finding(
                            kind=REDUNDANT_CALL,
                            index=record.index,
                            detail=(
                                f"tool {record.tool!r} repeats the identical call "
                                f"at index {records[prev_pos].index} with no state "
                                f"change between them"
                            ),
                        )
                    )
        else:
            seen_response[call] = response

        last_seen_index[call] = record.index
