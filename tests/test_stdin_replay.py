"""G8: stdin-aware replay - one case per verdict class, plus back-compat."""

from toolreplay.findings import NON_DETERMINISM
from toolreplay.replay import WORLD_CHANGE, replay
from toolreplay.transcript import parse_text

CALL = '{"command": "claude -p"}'


def _line(index, response, stdin=None):
    row = {"index": index, "tool": "run_command",
           "args": {"command": "claude -p"}, "response": {"out": response}}
    if stdin is not None:
        row["stdin_sha256"] = stdin
    import json
    return json.dumps(row)


def test_same_stdin_divergence_is_non_determinism():
    text = "\n".join([_line(0, "ok", "aaaa1111"), _line(1, "boom", "aaaa1111")])
    result = replay(parse_text(text))
    kinds = [f.kind for f in result.findings]
    assert kinds == [NON_DETERMINISM], kinds
    assert result.divergence_index == 1


def test_cross_stdin_divergence_is_world_change():
    text = "\n".join([_line(0, "ok", "aaaa1111"), _line(1, "boom", "bbbb2222")])
    result = replay(parse_text(text))
    kinds = [f.kind for f in result.findings]
    assert kinds == [WORLD_CHANGE], kinds
    assert result.divergence_index is None
    assert "(0, 1)" in result.findings[0].detail


def test_legacy_rows_without_stdin_behave_exactly_as_before():
    text = "\n".join([_line(0, "ok"), _line(1, "boom")])
    result = replay(parse_text(text))
    assert [f.kind for f in result.findings] == [NON_DETERMINISM]
    assert result.divergence_index == 1


def test_optional_field_round_trips_and_is_validated():
    (record,) = parse_text(_line(0, "ok", "aaaa1111"))
    assert record.stdin_sha256 == "aaaa1111"
    assert parse_text(_line(0, "ok"))[0].stdin_sha256 is None
    try:
        parse_text('{"index":0,"tool":"t","args":{},"response":{},"stdin_sha256":7}')
    except Exception as exc:
        assert "stdin_sha256 must be a string" in str(exc)
    else:
        raise AssertionError("non-string stdin_sha256 must be rejected")
