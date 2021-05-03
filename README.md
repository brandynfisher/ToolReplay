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
