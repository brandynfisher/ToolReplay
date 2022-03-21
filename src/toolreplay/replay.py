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
