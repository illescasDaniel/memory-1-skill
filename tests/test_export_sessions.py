import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import SCRIPTS, load

ex = load("export_sessions")


def jl(path, events):
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


class RedactTests(unittest.TestCase):
    def test_secrets_are_redacted(self):
        # Fake, obviously synthetic values built at runtime so no real-looking secret sits in the repo.
        cases = {
            "openai": "key sk-" + "a" * 30,
            "github": "ghp_" + "A1" * 15,
            "aws": "AKIA" + "ABCDEFGHIJKLMNOP",
            "jwt": "eyJ" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12,
            "bearer": "Authorization: Bearer " + "x" * 30,
            "assign": "API_KEY=" + "supersecret123",
            "url": "postgres://user:hunter22@db.example/x",
            "pem": "-----BEGIN RSA PRIVATE KEY-----\nabc\n-----END RSA PRIVATE KEY-----",
        }
        for label, text in cases.items():
            with self.subTest(label):
                out = ex.redact(text)
                self.assertIn("[REDACTED]", out)
        self.assertNotIn("hunter22", ex.redact(cases["url"]))
        self.assertNotIn("supersecret123", ex.redact(cases["assign"]))
        self.assertNotIn("abc", ex.redact(cases["pem"]))

    def test_plain_text_untouched(self):
        s = "We chose SQLite because it needs no server. See notes/db.md."
        self.assertEqual(ex.redact(s), s)

    def test_clip(self):
        self.assertEqual(ex.clip("abc", 10), "abc")
        self.assertEqual(ex.clip("abc", 0), "abc")
        self.assertIn("7 more characters", ex.clip("x" * 10, 3))


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_claude_reader_filters(self):
        p = self.tmp / "s.jsonl"
        jl(p, [
            {"type": "user", "timestamp": "2026-01-01T10:00:00Z", "message": {"content": "hello"}},
            {"type": "assistant", "timestamp": "2026-01-01T10:00:01Z",
             "message": {"content": [{"type": "text", "text": "hi"}, {"type": "tool_use", "name": "x"}]}},
            {"type": "user", "isSidechain": True, "message": {"content": "sub"}},
            {"type": "user", "isMeta": True, "message": {"content": "meta"}},
            {"type": "system", "message": {"content": "sys"}},
        ])
        with p.open("a") as f:
            f.write("not json\n")
        self.assertEqual([(r, t) for r, _, t in ex.read_claude(p)], [("user", "hello"), ("assistant", "hi")])

    def test_codex_reader(self):
        p = self.tmp / "rollout.jsonl"
        msg = lambda role, kind, text: {"type": "response_item", "timestamp": "t",
                                         "payload": {"type": "message", "role": role, "content": [{"type": kind, "text": text}]}}
        jl(p, [msg("user", "input_text", "q"), msg("assistant", "output_text", "a"), msg("developer", "input_text", "d"),
               {"type": "response_item", "payload": {"type": "reasoning"}}])
        self.assertEqual([(r, t) for r, _, t in ex.read_codex(p)], [("user", "q"), ("assistant", "a")])

    def test_render_skips_injected_and_needs_user_turn(self):
        p = self.tmp / "abcdef12-0000.jsonl"
        jl(p, [
            {"type": "user", "timestamp": "2026-02-03T09:00:00Z", "message": {"content": "<system-reminder>x</system-reminder>"}},
            {"type": "user", "timestamp": "2026-02-03T09:01:00Z", "message": {"content": "use token=" + "s3cretvalue99"}},
            {"type": "assistant", "timestamp": "2026-02-03T09:02:00Z", "message": {"content": "ok"}},
        ])
        name, body = ex.render("claude", p, ex.read_claude, 6000)
        self.assertEqual(name, "2026-02-03-abcdef12.md")
        self.assertNotIn("system-reminder", body)
        self.assertNotIn("s3cretvalue99", body)
        self.assertIn("2 messages", body)
        only_assistant = self.tmp / "b.jsonl"
        jl(only_assistant, [{"type": "assistant", "timestamp": "t", "message": {"content": "x"}}])
        self.assertEqual(ex.render("claude", only_assistant, ex.read_claude, 6000), (None, None))


class InsideTests(unittest.TestCase):
    def test_inside(self):
        self.assertTrue(ex.inside("/a/b", Path("/a/b")))
        self.assertTrue(ex.inside("/a/b/c", Path("/a/b")))
        self.assertFalse(ex.inside("/a/bc", Path("/a/b")))
        self.assertFalse(ex.inside(None, Path("/a/b")))


class EnsureIgnoredTests(unittest.TestCase):
    def test_adds_line_once(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        out = tmp / "memory" / "sessions"
        out.mkdir(parents=True)
        ex.ensure_ignored(out)
        ex.ensure_ignored(out)
        self.assertEqual((tmp / "memory" / ".gitignore").read_text(), "/sessions\n")


class EndToEndTests(unittest.TestCase):
    """Run the real script as a subprocess against a fake Claude Code store; HOME is isolated."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.project = self.tmp / "proj"
        self.project.mkdir()
        self.home = self.tmp / "home"
        enc = "".join(c if c.isalnum() else "-" for c in str(self.project.resolve()))
        self.store = self.home / ".claude" / "projects" / enc
        self.store.mkdir(parents=True)
        jl(self.store / "11111111-aaaa.jsonl", [
            {"type": "user", "cwd": str(self.project.resolve()), "timestamp": "2026-03-01T08:00:00Z",
             "message": {"content": "decide on X"}},
            {"type": "assistant", "timestamp": "2026-03-01T08:00:05Z", "message": {"content": "X it is"}},
        ])
        self.env = {**os.environ, "HOME": str(self.home), "CLAUDE_CONFIG_DIR": str(self.home / ".claude"),
                    "CODEX_HOME": str(self.home / ".codex"), "XDG_DATA_HOME": str(self.home / "share")}

    def run_script(self, *extra):
        return subprocess.run([sys.executable, "-I", str(SCRIPTS / "export_sessions.py"), "--project", str(self.project), *extra],
                              capture_output=True, text=True, env=self.env, cwd=self.tmp)

    def test_export_is_idempotent(self):
        out = self.tmp / "out"
        r = self.run_script("--out", str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        f = out / "2026-03-01-11111111.md"
        self.assertTrue(f.is_file())
        self.assertIn("X it is", f.read_text())
        self.assertIn("1 new", r.stderr)
        r2 = self.run_script("--out", str(out))
        self.assertIn("1 unchanged", r2.stderr)
        self.assertEqual(r2.stdout.strip(), "")

    def test_dry_run_writes_nothing_and_since_filters(self):
        out = self.tmp / "out"
        r = self.run_script("--out", str(out), "--dry-run")
        self.assertIn("new", r.stdout)
        self.assertFalse(out.exists())
        r = self.run_script("--out", str(out), "--since", "2027-01-01")
        self.assertIn("0 new", r.stderr)

    def test_no_sessions_exits_1(self):
        shutil.rmtree(self.store)
        r = self.run_script("--out", str(self.tmp / "out"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("no Claude Code", r.stderr)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_default_out_in_git_repo_adds_gitignore(self):
        subprocess.run(["git", "init", "-q", str(self.project)], check=True)
        r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "export_sessions.py"), "--project", str(self.project)],
                           capture_output=True, text=True, env=self.env, cwd=self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.project / "memory" / "sessions" / "2026-03-01-11111111.md").is_file())
        self.assertEqual((self.project / "memory" / ".gitignore").read_text(), "/sessions\n")


if __name__ == "__main__":
    unittest.main()
