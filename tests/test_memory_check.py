import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import SKILL, load

mc = load("memory_check")

NOTE = """---
name: {name}
description: d
type: decision
date: 2026-01-01
status: {status}
supersedes: {sup}
superseded_by: {by}
source:
---
body
"""


def run(mem):
    out = io.StringIO()
    argv = ["memory_check.py", "--memory", str(mem)]
    with mock.patch("sys.argv", argv), contextlib.redirect_stdout(out):
        code = mc.main()
    return code, out.getvalue()


class MemoryCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.mem = self.tmp / "memory"
        (self.mem / "notes").mkdir(parents=True)
        (self.mem / "NOW.md").write_text("# Now\nUpdated: 2026-01-01\n\n## Doing\n- x\n")
        (self.mem / "MEMORY.md").write_text("# Memory\n")

    def note(self, name, status="current", sup="", by="", indexed=True):
        (self.mem / "notes" / f"{name}.md").write_text(NOTE.format(name=name, status=status, sup=sup, by=by))
        if indexed:
            with (self.mem / "MEMORY.md").open("a") as f:
                f.write(f"- [{name}](notes/{name}.md) - d\n")

    def test_clean_memory_passes(self):
        self.note("a")
        code, out = run(self.mem)
        self.assertEqual(code, 0, out)
        self.assertIn("1 notes", out)
        self.assertIn("0 to fix", out)

    def test_missing_folder_exits(self):
        with mock.patch("sys.argv", ["x", "--memory", str(self.tmp / "nope")]):
            with self.assertRaises(SystemExit) as cm:
                mc.main()
        self.assertIn("no memory folder", str(cm.exception))

    def test_missing_now(self):
        (self.mem / "NOW.md").unlink()
        code, out = run(self.mem)
        self.assertEqual(code, 1)
        self.assertIn("NOW.md is missing", out)

    def test_now_too_long_and_extra_section(self):
        (self.mem / "NOW.md").write_text("# Now\n## Doing\n" + "- x\n" * 60 + "## Backlog\n")
        code, out = run(self.mem)
        self.assertEqual(code, 1)
        self.assertIn("lines (limit 50)", out)
        self.assertIn("extra sections (Backlog)", out)

    def test_too_many_next_items(self):
        (self.mem / "NOW.md").write_text("# Now\n## Next\n" + "".join(f"- {i}\n" for i in range(8)))
        _, out = run(self.mem)
        self.assertIn("Next has 8 items", out)

    def test_unindexed_note(self):
        self.note("a", indexed=False)
        code, out = run(self.mem)
        self.assertEqual(code, 1)
        self.assertIn("not listed in MEMORY.md", out)

    def test_note_listed_in_topic_page_counts_as_indexed(self):
        self.note("a", indexed=False)
        (self.mem / "topics").mkdir()
        (self.mem / "topics" / "t.md").write_text("- [a](../notes/a.md)\n")
        code, out = run(self.mem)
        self.assertEqual(code, 0, out)

    def test_missing_frontmatter(self):
        (self.mem / "notes" / "bad.md").write_text("no frontmatter\n")
        _, out = run(self.mem)
        self.assertIn("no frontmatter", out)

    def test_underscore_notes_ignored(self):
        (self.mem / "notes" / "_example.md").write_text("junk")
        code, out = run(self.mem)
        self.assertEqual(code, 0, out)

    def test_supersession_problems(self):
        self.note("old", status="superseded", by="")           # superseded with no replacement
        self.note("new", sup="ghost")                           # points at a missing note
        self.note("mid", status="current", by="new")            # superseded_by but status current
        _, out = run(self.mem)
        self.assertIn("superseded_by is empty", out)
        self.assertIn("supersedes ghost is not a note", out)
        self.assertIn("set status: superseded", out)

    def test_valid_supersession(self):
        self.note("old", status="superseded", by="new")
        self.note("new", sup="old")
        code, out = run(self.mem)
        self.assertEqual(code, 0, out)

    def test_broken_index_link(self):
        with (self.mem / "MEMORY.md").open("a") as f:
            f.write("- [x](notes/missing.md)\n- [web](https://e.com/a.md)\n")
        _, out = run(self.mem)
        self.assertIn("link to notes/missing.md is broken", out)
        self.assertNotIn("e.com", out)

    def test_index_too_long(self):
        (self.mem / "MEMORY.md").write_text("# Memory\n" + "x\n" * 160)
        _, out = run(self.mem)
        self.assertIn("create topic pages", out)

    def test_later_checks(self):
        rows = "".join(f"- (Mine) 2026-01-01 s{i}\n" for i in range(9))
        (self.mem / "LATER.md").write_text(
            "# Later\n## Suggestions\n" + rows + "## Other\n- (User) 2025-01-01 old thing\n- (Mine) stray\n"
            + "- " + "y" * 250 + "\n")
        _, out = run(self.mem)
        self.assertIn("9 suggestions (limit 8)", out)
        self.assertIn("older than 30 days", out)
        self.assertIn("(User) line(s) older than", out)
        self.assertIn("(Mine) line(s) outside", out)
        self.assertIn("over 240 characters", out)

    def test_shipped_templates_pass(self):
        mem = self.tmp / "tpl"
        shutil.copytree(SKILL / "templates", mem)
        (mem / "notes" / "_example.md").unlink()  # the example is a template, not a note
        code, out = run(mem)
        self.assertEqual(code, 0, out)


class HelperTests(unittest.TestCase):
    def test_items(self):
        text = "## Next\n- a\n2. b\ntext\n## Done\n- c\n"
        self.assertEqual(mc.items(text, "Next"), ["- a", "2. b"])
        self.assertEqual(mc.items(text, "Nope"), [])

    def test_meta(self):
        p = Path(tempfile.mkdtemp()) / "n.md"
        p.write_text("---\nname: a\nstatus: current\n---\nbody")
        self.assertEqual(mc.meta(p), {"name": "a", "status": "current"})
        p.write_text("plain")
        self.assertIsNone(mc.meta(p))


if __name__ == "__main__":
    unittest.main()
