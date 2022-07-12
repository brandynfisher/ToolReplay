"""argparse CLI with subcommands.

Subcommands:
    seal      read a transcript, print the hash-chained sealed JSONL
    replay    replay a transcript, report non-determinism and redundant calls
    verify    verify a sealed JSONL chain is intact
    scope     check a transcript against a declared scope file
    version   print the version

Exit codes: 0 clean, 1 findings present or chain broken, 2 usage error.
"""

import argparse
import sys

from toolreplay import __version__
from toolreplay import chain, replay, report, scope, transcript
from toolreplay.transcript import TranscriptError
from toolreplay.scope import ScopeError


EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


def _load_records(path: str):
    return transcript.load(path)


def cmd_seal(args) -> int:
    records = _load_records(args.transcript)
    links = chain.seal(records)
    sys.stdout.write(chain.links_to_jsonl(links))
    return EXIT_CLEAN


def cmd_replay(args) -> int:
    records = _load_records(args.transcript)
    result = replay.replay(records)
    sys.stdout.write(
        report.render_report(result.findings, result.divergence_index, result.call_count)
    )
    return EXIT_FINDINGS if result.findings else EXIT_CLEAN


def cmd_verify(args) -> int:
    links = chain.load_sealed(args.sealed)
    result = chain.verify(links)
    sys.stdout.write(
        report.render_verify_report(
            result.ok, result.broken_index, result.expected, result.found
        )
    )
    return EXIT_CLEAN if result.ok else EXIT_FINDINGS


def cmd_scope(args) -> int:
    records = _load_records(args.transcript)
    declared = scope.load(args.scope)
    findings = scope.detect_overreach(records, declared)
    sys.stdout.write(report.render_scope_report(findings, len(records)))
    return EXIT_FINDINGS if findings else EXIT_CLEAN


def cmd_version(args) -> int:
