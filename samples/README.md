# Sample fixtures

These files are hand-authored test vectors, not captured production data. They
exist to exercise every code path in toolreplay. Each is described below.

## scope.json

Declares an agent `docs-reader` permitted to call `read_file`, `list_dir`, and
`search`. It deliberately does not permit `write_file`, so any write in a
session is permission overreach.
