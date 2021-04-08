# Changelog

All notable changes to this project are documented here.

## 0.6.0 - 2026-03-12

- Argument-aware scope groundwork: scope files accept an optional `target`
  allow-list per tool; matching stays exact and case-sensitive.
- `scope` reports now name the offending tool and the agent it belongs to.
- Samples: `session-dirty.jsonl` extended with a scope-mismatch call.

## 0.5.0 - 2025-06-18

- `seal` / `verify` hash chain is now stable across Python 3.11 and 3.12:
