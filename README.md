# ToolReplay

ToolReplay audits a recorded transcript of an AI agent's tool calls and reports where the
session was non-deterministic, redundant, or outside its declared permissions.

Here is the tool working, right now, on the dirty sample that ships in this repository. The
command is shown above its output, and the output is pasted verbatim from a run in this
checkout:

```
$ python -m toolreplay replay samples/session-dirty.jsonl
calls: 6
divergence: index 5
findings: 2
index 2: redundant-call: tool 'read_file' repeats the identical call at index 1 with no state change between them
index 5: non-determinism: tool 'search' returned a different response than the identical call at index 3
exit code: 1
```

## What just happened

Those three header lines and two findings are the whole audit of a six-call session. Read
them top to bottom.

`calls: 6` is the number of records parsed from `samples/session-dirty.jsonl`. Parsing is
strict, so a six here means six well-formed lines with indices 0 through 5 and nothing
malformed.

`divergence: index 5` is the first index where a deterministic re-run would disagree with
the record. The tool found that index 5 repeated an earlier call but carried a different
recorded response, so that is the earliest point the session stops being reproducible.

`findings: 2` counts the audit results below the header. They are printed in a fixed order,
sorted by index then by kind, so the same input always prints byte-identical output.

The first finding, at index 2, is a redundant call: `read_file` on `docs/intro.md` was
already made at index 1, and nothing between the two could have changed the file, so the
second read did no new work. The second finding, at index 5, is non-determinism: the
`search` for `install` returned 3 hits at index 3 and 7 hits at index 5, from the identical
call. The process exited 1 because findings were present.

The scope check is a separate command, because scope needs a declared permission file that
replay does not. Run against the same session and the shipped scope file, it finds the one
call that stepped outside the agent's declared tools:

```
$ python -m toolreplay scope samples/session-dirty.jsonl samples/scope.json
calls: 6
findings: 1
index 4: permission-overreach: tool 'write_file' is not in the declared scope for agent 'docs-reader'
```

Between replay and scope, all three finding types this tool detects are present in that one
six-line sample.

## Install

toolreplay needs Python 3.11 or newer and has no third-party runtime dependencies. It does
no network access. You can run it straight from a source checkout:

```
python -m toolreplay version
```

Or install the console script and call it by name:

```
pip install .
toolreplay version
```

Both print the same line:

```
$ python -m toolreplay version
toolreplay 0.6.0
```

## Commands

| Command                        | What it does                                                    | Reads            |
| ------------------------------ | --------------------------------------------------------------- | ---------------- |
| `seal <transcript>`            | Print the hash-chained sealed transcript as JSONL               | a transcript     |
| `replay <transcript>`          | Report non-determinism, redundant calls, and the divergence     | a transcript     |
| `verify <sealed>`              | Recompute the chain and report the first broken link            | a sealed file    |
| `scope <transcript> <scope>`   | Check every call against a declared scope file                  | transcript+scope |
| `version`                      | Print the version                                               | nothing          |

`replay` and `scope` are deliberately separate. Replay judges a session against itself and
needs no external input. Scope judges a session against a permission declaration you supply,
so it takes a second file. Keeping them apart means you can replay a session you have no
scope file for, and you can check scope without caring whether the session replayed cleanly.

## The three findings it detects

Each finding type has a rule, a real example from `samples/session-dirty.jsonl`, and a
reason it matters when the transcript came from an agent rather than a person.

### Non-determinism

Rule: the first time a call appears, its recorded response is remembered. If the same call
(same tool name, same arguments after canonical JSON encoding) appears again with a
different recorded response, that is non-determinism. The first such index becomes the
divergence point.

Real example: index 3 and index 5 are both `search` for `install`. Index 3 recorded
`{"hits": 3}` and index 5 recorded `{"hits": 7}`. Those are the same question with two
answers, so the tool reports non-determinism at index 5 and marks it the divergence point.

Why it matters for an agent: an agent that asks the same question twice and gets two answers
cannot be replayed or debugged reliably. The step that used the first answer may have made a
decision that the second answer would have changed. Non-determinism is the signal that a
session's outcome depends on something outside the recorded inputs.

### Redundant call

Rule: two identical calls are redundant only when nothing between them could have changed
state. A call is a possible state change if its tool is a mutator, or if it is any call
different from the repeated one. The default mutators are `write_file`, `delete_file`,
`create_file`, `move_file`, and `run_command`. This is deliberately conservative: it would
rather miss a redundancy than invent one.

Real example: index 1 and index 2 are both `read_file` on `docs/intro.md`, adjacent, with
nothing between them. The second read learned nothing the first did not, so index 2 is
flagged redundant. Note the contrast at the file level: index 4 writes the same file, so a
later read after index 4 would not be redundant, because the write may have moved the world.

Why it matters for an agent: redundant calls are wasted tokens and wasted latency, and they
often mean the agent lost track of what it already knew. One repeat is cheap. A loop of
repeats is a stuck agent burning budget.

### Permission overreach

Rule: each call's tool name is compared against the `allowed_tools` list in the scope file,
matched exactly and case-sensitively. Any tool not in the list is overreach. A scope that
quietly accepted near-matches like `Read_File` for `read_file` would not be a scope, so the
match is strict.

Real example: `samples/scope.json` permits `read_file`, `list_dir`, and `search` for the
agent `docs-reader`. Index 4 calls `write_file`, which is not on the list, so it is reported
as overreach for `docs-reader`.

Why it matters for an agent: a read-only agent that writes a file has exceeded the authority
it was given, whether through a prompt injection, a planning error, or a misconfigured tool
set. Overreach is the audit result that maps directly to a security question: did this agent
only do what it was allowed to do?

## The transcript format

