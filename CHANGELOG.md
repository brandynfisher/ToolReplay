# Changelog

All notable changes to this project are documented here.

## 0.6.0 - 2026-03-12

- Argument-aware scope groundwork: scope files accept an optional `target`
  allow-list per tool; matching stays exact and case-sensitive.
- `scope` reports now name the offending tool and the agent it belongs to.
- Samples: `session-dirty.jsonl` extended with a scope-mismatch call.

## 0.5.0 - 2025-06-18

- `seal` / `verify` hash chain is now stable across Python 3.11 and 3.12:
  canonical encoding uses `sort_keys` and separators explicitly.
- `verify` prints the expected and found digest of the first broken link.
- CLI: uniform exit codes (0 clean, 1 findings, 2 usage/parse error).

## 0.4.0 - 2024-07-03

- `replay` detects non-determinism between identical calls with different
  recorded responses; the first such index is the divergence point.
- Redundancy detection respects mutator tools (`write_file`, `delete_file`,
  `create_file`, `move_file`, `run_command`).
- `scope` command added for declared-tools overreach checks.

## 0.3.0 - 2023-08-11

- SHA-256 hash chaining with genesis link and tamper verification in `chain.py`.
- `seal` and `verify` subcommands; sealed transcripts are JSON Lines.
- `findings.py` with fixed ordering: index, then kind.

## 0.2.0 - 2022-05-20

- Strict JSONL transcript parsing in `transcript.py`: unknown fields, bad
  indices, and non-object args/responses are hard errors.
- Canonical call encoding (`{"tool", "args"}` with sorted keys) used for
  byte-exact comparison.

## 0.1.0 - 2021-06-14

- First release: transcript model, line-oriented `report.py`, CLI skeleton,
  and the first hand-authored sample fixtures.

<!-- draft note 610 -->
