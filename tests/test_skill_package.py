"""Sanity checks on the installable skill folder itself."""
import re
import unittest

from helpers import SKILL


class SkillPackageTests(unittest.TestCase):
    def test_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text()
        m = re.match(r"---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(m)
        fm = m.group(1)
        self.assertRegex(fm, r"(?m)^name: memory-1$")
        self.assertRegex(fm, r"(?m)^description: .{50,}")
        self.assertRegex(fm, r"(?m)^license: MIT$")

    def test_referenced_files_exist(self):
        text = (SKILL / "SKILL.md").read_text()
        for rel in set(re.findall(r"\b((?:scripts|templates)/[\w./-]+\.(?:py|md))", text)):
            with self.subTest(rel):
                self.assertTrue((SKILL / rel).exists(), rel)

    def test_scripts_compile(self):
        for p in (SKILL / "scripts").glob("*.py"):
            compile(p.read_text(), str(p), "exec")

    def test_templates_present(self):
        for rel in ("NOW.md", "LATER.md", "MEMORY.md", ".gitignore", "sessions/INDEX.md", "notes/_example.md"):
            self.assertTrue((SKILL / "templates" / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
