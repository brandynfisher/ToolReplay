import contextlib
import io
import json
import os
import tempfile
import unittest

from toolreplay import chain, cli, transcript
from toolreplay.chain import Anchor, GENESIS
from toolreplay.transcript import TranscriptError


SAMPLE = "".join(
    '{"index":%d,"tool":"read_file","args":{"p":"a"},"response":{"n":%d}}\n' % (i, i)
    for i in range(4)
)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


def write_temp(text):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


class TestSealedValidation(unittest.TestCase):
    def test_anchor_line_is_written(self):
        links = chain.seal(transcript.parse_text(SAMPLE))
        text = chain.links_to_jsonl(links)
        last = json.loads(text.splitlines()[-1])
        self.assertEqual(last["count"], 4)
        self.assertEqual(last["head"], links[-1].digest)

    def test_truncation_is_detected(self):
        text = chain.links_to_jsonl(chain.seal(transcript.parse_text(SAMPLE)))
        lines = text.splitlines()
        # Drop the last record but leave the original anchor in place.
        kept = lines[:-2] + [lines[-1]]
        path = write_temp("\n".join(kept) + "\n")
        try:
            code, out, _ = run(["verify", path])
            self.assertEqual(code, 1)
            self.assertIn("chain: broken", out)
            self.assertIn("record count", out)
        finally:
            os.remove(path)

    def test_extra_field_is_rejected(self):
        text = chain.links_to_jsonl(chain.seal(transcript.parse_text(SAMPLE)))
        lines = []
        for line in text.splitlines():
            obj = json.loads(line)
            obj["note"] = "not covered"
            lines.append(json.dumps(obj, sort_keys=True))
        path = write_temp("\n".join(lines) + "\n")
        try:
            with self.assertRaises(TranscriptError):
                chain.verify_file(path)
        finally:
            os.remove(path)

    def test_malformed_json_is_usage_error(self):
        path = write_temp("not json\n")
        try:
            code, _, err = run(["verify", path])
            self.assertEqual(code, 2)
            self.assertIn("invalid JSON", err)
        finally:
            os.remove(path)

    def test_unanchored_file_is_reported_as_unanchored(self):
        links = chain.seal(transcript.parse_text(SAMPLE))
        lines = [
            json.dumps(
                {
                    "index": link.index,
                    "prev": link.prev,
                    "digest": link.digest,
                    "tool": link.record.tool,
                    "args": link.record.args,
                    "response": link.record.response,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            for link in links
        ]
        path = write_temp("\n".join(lines) + "\n")
        try:
            code, out, _ = run(["verify", path])
            self.assertEqual(code, 0)
            self.assertIn("chain: intact (unanchored)", out)
        finally:
            os.remove(path)

    def test_pinned_head_detects_full_reseal(self):
        records = transcript.parse_text(SAMPLE)
        original = chain.seal(records)
        shorter_records = transcript.parse_text(
            "".join('{"index":%d,"tool":"t","args":{},"response":{}}\n' % i for i in range(3))
        )
        shorter = chain.seal(shorter_records)
        result = chain.verify(shorter, Anchor(count=3, head=original[-1].digest))
        self.assertFalse(result.ok)
        self.assertIn("final digest", result.anchor_error or "")

    def test_empty_chain_has_genesis_head(self):
        text = chain.links_to_jsonl([])
        anchor = json.loads(text.splitlines()[-1])
        self.assertEqual(anchor["head"], GENESIS)
        self.assertEqual(anchor["count"], 0)


if __name__ == "__main__":
    unittest.main()
