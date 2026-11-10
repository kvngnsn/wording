#!/usr/bin/env python3
"""Safety and integrity checks in synthetic temporary homes only."""

from pathlib import Path
import tempfile
import unittest
import zipfile

import skills


class SkillToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wording-tools-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        for name in skills.NAMES:
            folder = self.root / "skills" / name
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text(
                f'---\nname: {name}\ndescription: "Write a clear synthetic example."\n---\n\n'
                'Use the supplied facts.\n', encoding="utf-8")
        self.first = self.root / "skills" / skills.NAMES[0]

    def test_dry_run_writes_no_discovery_directories(self):
        plan = skills.install(self.root)
        self.assertEqual(len(plan), 12)
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_symlink_install_and_idempotent_rerun(self):
        skills.install(self.root, apply=True)
        skills.validate_installed(self.root)
        rerun = skills.install(self.root, apply=True)
        self.assertTrue(all(action == "unchanged" for action, _, _ in rerun))
        for provider in skills.PROVIDERS.values():
            link = self.root / provider / "skills" / skills.NAMES[0]
            self.assertFalse(link.readlink().is_absolute())
        relocated = self.root.with_name("relocated")
        self.root.rename(relocated)
        skills.validate_installed(relocated)

    def test_all_collisions_preflight_before_any_new_mapping(self):
        directory = self.root / ".claude" / "skills"
        directory.mkdir(parents=True)
        collision = directory / skills.NAMES[-1]
        collision.write_text("preserve this unrelated file", encoding="utf-8")
        with self.assertRaises(skills.SkillError):
            skills.install(self.root, apply=True)
        self.assertFalse((self.root / ".agents").exists())
        self.assertEqual(collision.read_text(), "preserve this unrelated file")

    def test_broken_link_is_a_collision(self):
        directory = self.root / ".agents" / "skills"
        directory.mkdir(parents=True)
        collision = directory / skills.NAMES[0]
        collision.symlink_to(self.root / "missing")
        with self.assertRaises(skills.SkillError):
            skills.install(self.root, apply=True)
        self.assertTrue(collision.is_symlink())
        self.assertFalse((self.root / ".claude").exists())

    def test_user_scope_can_be_isolated_in_synthetic_home(self):
        skills.install(self.root, scope="user", home=self.home, apply=True)
        skills.validate_installed(self.root, scope="user", home=self.home)
        self.assertFalse((self.root / ".agents").exists())
        self.assertTrue((self.home / ".claude/skills" / skills.NAMES[0]).is_symlink())

    def test_parent_symlink_cannot_redirect_install(self):
        (self.root / ".agents").symlink_to(self.home, target_is_directory=True)
        with self.assertRaises(skills.SkillError):
            skills.install(self.root, apply=True)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_copy_is_a_snapshot_and_never_overwrites(self):
        skills.install(self.root, apply=True, copy=True)
        dest = self.root / ".agents/skills" / skills.NAMES[0]
        self.assertFalse(dest.is_symlink())
        skills.validate_installed(self.root)
        (dest / "SKILL.md").write_text("user's changed copy", encoding="utf-8")
        with self.assertRaises(skills.SkillError):
            skills.install(self.root, apply=True, copy=True)
        with self.assertRaises(skills.SkillError):
            skills.validate_installed(self.root)
        self.assertEqual((dest / "SKILL.md").read_text(), "user's changed copy")

    def test_invalid_metadata_is_rejected(self):
        path = self.first / "SKILL.md"
        valid = path.read_text()
        for invalid in [
            valid.replace(skills.NAMES[0], "different-name", 1),
            valid.replace("description:", "name: duplicate\ndescription:"),
            valid.replace('"Write a clear synthetic example."', "false"),
            valid.replace('"Write a clear synthetic example."', '"' + 'x' * 201 + '"'),
            valid.replace("Use the supplied facts.", "TODO: fill this in."),
        ]:
            path.write_text(invalid, encoding="utf-8")
            with self.subTest(invalid=invalid):
                with self.assertRaises(skills.SkillError):
                    skills.validate_skill(self.first)
        path.write_text(valid, encoding="utf-8")

    def test_folded_description_and_relative_reference(self):
        path = self.first / "SKILL.md"
        text = path.read_text().replace('description: "Write a clear synthetic example."',
                                        "description: >-\n  Write a clear\n  synthetic example.")
        (self.first / "references").mkdir()
        (self.first / "references/example.md").write_text("A real example.")
        path.write_text(text + "\nSee [example](references/example.md).\n")
        self.assertEqual(skills.validate_skill(self.first)["description"],
                         "Write a clear synthetic example.")

    def test_missing_and_escaping_references_are_rejected(self):
        path = self.first / "SKILL.md"
        original = path.read_text()
        for ref in ["references/missing.md", "../../../../outside.md"]:
            path.write_text(original + f"\n[reference]({ref})\n")
            with self.assertRaises(skills.SkillError):
                skills.validate_skill(self.first)

    def test_package_layout_content_and_collision(self):
        output = self.home / "uploads"
        written = skills.package(self.root, output)
        self.assertEqual(len(written), 6)
        for archive in written:
            folder = self.root / "skills" / archive.stem
            skills.validate_zip(archive, folder)
            with zipfile.ZipFile(archive) as z:
                self.assertEqual(z.namelist(), [archive.stem + "/SKILL.md"])
        before = {p.name: p.read_bytes() for p in written}
        with self.assertRaises(skills.SkillError):
            skills.package(self.root, output)
        self.assertEqual(before, {p.name: p.read_bytes() for p in written})

    def test_internal_symlink_is_not_a_portable_bundle(self):
        (self.first / "outside").symlink_to(self.home, target_is_directory=True)
        with self.assertRaises(skills.SkillError):
            skills.validate_skill(self.first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
