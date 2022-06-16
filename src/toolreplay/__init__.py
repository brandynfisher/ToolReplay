"""toolreplay: audit AI agent tool-call traces.

Ingests a JSON Lines session transcript of tool invocations, rewrites it as a
hash-chained record so tampering is detectable, then replays the session
deterministically against the recorded responses to surface non-determinism,
