# Contributing to ToolReplay

Thanks for looking at ToolReplay. This project audits recorded tool calls, so
the bar for changes is: the tool must stay deterministic, dependency-free at
runtime, and honest about what it cannot see.

## Ground rules

- Runtime code must not add third-party dependencies and must not do network
  access. The audit must stay pure and reproducible.
- Reports must remain deterministic and timestamp-free; two runs on the same
  input must diff to nothing.
- Prefer refusing malformed input over guessing. A parser that silently
  repairs its input cannot be trusted to report what the input said.

## Workflow

1. Fork the repo and branch from `main` (`fix/...`, `feat/...`).
2. Keep the change small and one topic per commit.
3. Run the suite before opening a pull request:

   ```
   python -m pip install -e .
   python -m unittest discover -s tests
   ```

4. Update `CHANGELOG.md` under a new version heading when behaviour changes.
5. Open a pull request describing the change and the output difference.

## Reporting bugs

Open an issue with the exact command, the input file (or a minimal version of
it), the output you saw, and the output you expected.
