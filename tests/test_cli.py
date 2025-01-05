import contextlib
import io
import unittest

from toolreplay import cli


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def test_version(self):
        code, out, _ = run(["version"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("toolreplay "))

    def test_replay_clean_exit_zero(self):
        code, out, _ = run(["replay", "samples/session-clean.jsonl"])
        self.assertEqual(code, 0)
        self.assertIn("divergence: none", out)
        self.assertIn("findings: 0", out)

    def test_replay_dirty_exit_one(self):
        code, out, _ = run(["replay", "samples/session-dirty.jsonl"])
        self.assertEqual(code, 1)
        self.assertIn("divergence: index 5", out)
        self.assertIn("redundant-call", out)
        self.assertIn("non-determinism", out)
