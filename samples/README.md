# Sample fixtures

These files are hand-authored test vectors, not captured production data. They
exist to exercise every code path in toolreplay. Each is described below.

## scope.json

Declares an agent `docs-reader` permitted to call `read_file`, `list_dir`, and
`search`. It deliberately does not permit `write_file`, so any write in a
session is permission overreach.

## session-clean.jsonl

Four calls that replay cleanly: a directory listing, two distinct file reads,
and one search. No identical call repeats, so there is no non-determinism and
no redundancy. Every tool used is inside the declared scope.

## session-dirty.jsonl

Six calls constructed to trigger one of each finding type:

- index 2 repeats the identical `read_file` from index 1 with nothing between
  them, so it is a redundant call.
- index 4 calls `write_file`, which is outside the `docs-reader` scope, so it
  is permission overreach.
- index 5 repeats the `search` from index 3 (same query) but the recorded
  response changed from 3 hits to 7 hits, so it is non-determinism. This is the
  first index where a deterministic replay would disagree with the record, so
  the CLI reports divergence at index 5.

<!-- draft note 652 -->
