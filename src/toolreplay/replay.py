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

# Same tool and args, different stdin, different response: the world moved
# under the call rather than the call being non-deterministic. Informational.
WORLD_CHANGE = "world-change"
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

    # Map canonical call (tool, args, stdin) -> response first seen for it.
    seen_response: dict[str, str] = {}
    # Map canonical call -> index it was last observed at.
    last_seen_index: dict[str, int] = {}
    # Map args-only call -> [(stdin, response, index)] observed so far.
    by_args: dict[str, list[tuple[str | None, str, int]]] = {}

    for pos, record in enumerate(records):
        call = record.canonical_key()
        args_call = record.canonical_call()
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
                    if records[back].canonical_key() == call:
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
            witness = _world_change_witness(
                by_args.get(args_call, ()), record.stdin_sha256, response
            )
            if witness is not None:
                findings.append(
                    Finding(
                        kind=WORLD_CHANGE,
                        index=record.index,
                        detail=(
                            f"tool {record.tool!r} ran with the same arguments as "
                            f"index {witness} but different stdin and a different "
                            f"response; replay the witness pair "
                            f"({witness}, {record.index})"
                        ),
                    )
                )
            seen_response[call] = response

        by_args.setdefault(args_call, []).append(
            (record.stdin_sha256, response, record.index)
        )
        last_seen_index[call] = record.index

    return ReplayResult(
        findings=findings,
        divergence_index=divergence_index,
        call_count=len(records),
    )


def _world_change_witness(prior, stdin_sha256, response):
    """Return the index of the earliest differing-stdin, differing-response call.

    None when every earlier call with these arguments either shared this stdin
    or returned the same response. Rows with no recorded stdin never match, so
    stdin-less transcripts produce no world-change findings.
    """
    if stdin_sha256 is None:
        return None
    for prior_stdin, prior_response, index in prior:
        if prior_stdin is None or prior_stdin == stdin_sha256:
            continue
        if prior_response != response:
            return index
    return None


def _no_state_change_between(
    records: list[Record],
    prev_pos: int,
    pos: int,
    call: str,
    mutators: frozenset[str],
) -> bool:
    """True when nothing between prev_pos and pos could have changed state.

    A mutator call between them, or any non-identical call, is treated as a
    possible state change, so the later call is not considered redundant.
    """
    for between in range(prev_pos + 1, pos):
        mid = records[between]
        if mid.tool in mutators:
            return False
        if mid.canonical_key() != call:
            return False
    return True
