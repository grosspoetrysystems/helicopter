from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "skills/helicopter/scripts"))

import check_install  # noqa: E402
import stage  # noqa: E402


def archive(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path, data in files.items():
            info = tarfile.TarInfo(f"helicopter-abc123/{path}")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def manifest(files: dict[str, bytes], version: str = "v0.2.0") -> dict:
    return {"version": version, "commit": "abc123", "files": {p: hashlib.sha256(d).hexdigest() for p, d in files.items()}}


RELEASE = {"CONTRIBUTING.md": b"rules\n", "scripts/validate_pr.py": b"code\n", "LICENSE": b"MIT\n"}


class Repository:
    """A scratch target and staging directory, filled with `files`."""

    def __init__(self, files: dict[str, bytes]):
        self.target_dir, self.staging_dir = tempfile.TemporaryDirectory(), tempfile.TemporaryDirectory()
        self.target, self.staging = Path(self.target_dir.name), Path(self.staging_dir.name)
        for path, data in files.items():
            (self.target / path).parent.mkdir(parents=True, exist_ok=True)
            (self.target / path).write_bytes(data)

    def read(self, path: str) -> bytes | None:
        return (self.target / path).read_bytes() if (self.target / path).is_file() else None

    def close(self) -> None:
        self.target_dir.cleanup()
        self.staging_dir.cleanup()


class InstallTests(unittest.TestCase):
    def test_the_install_paths_match_the_checker(self):
        self.assertEqual(stage.VERSION_MARKER, check_install.VERSION_MARKER)
        self.assertEqual(stage.INSTALL_PATHS, check_install.INSTALL_PATHS)

    def test_releases_before_the_skill_are_refused(self):
        self.assertFalse(stage.supported("v0.1.0"))
        self.assertFalse(stage.supported("garbage"))
        self.assertTrue(stage.supported("v0.2.0"))
        self.assertTrue(stage.supported("v1.0.0"))

    def test_archive_files_are_checked_against_the_manifest(self):
        self.assertEqual(stage.release_files(manifest(RELEASE), archive({**RELEASE, "README.md": b"x"})), RELEASE)
        tampered = archive({**RELEASE, "scripts/validate_pr.py": b"evil\n"})
        with self.assertRaisesRegex(SystemExit, "scripts/validate_pr.py"):
            stage.release_files(manifest(RELEASE), tampered)
        with self.assertRaisesRegex(SystemExit, "LICENSE"):
            stage.release_files(manifest(RELEASE), archive({p: d for p, d in RELEASE.items() if p != "LICENSE"}))

    def test_adds_missing_keeps_identical_and_stages_differences_without_overwriting(self):
        repo = Repository({"CONTRIBUTING.md": b"our own rules\n", "scripts/validate_pr.py": b"code\n"})
        self.addCleanup(repo.close)
        outcome = stage.stage(manifest(RELEASE), RELEASE, repo.target, repo.staging)

        self.assertEqual({k: v for k, v in outcome.items() if v}, {
            "added": [".github/helicopter/LICENSE"],
            "unchanged": ["scripts/validate_pr.py"],
            "differs": ["CONTRIBUTING.md"],
        })
        self.assertEqual(repo.read("CONTRIBUTING.md"), b"our own rules\n")
        self.assertEqual((repo.staging / "CONTRIBUTING.md").read_bytes(), b"rules\n")
        self.assertIsNone(repo.read("LICENSE"))
        self.assertEqual(json.loads(repo.read(stage.VERSION_MARKER)), {"version": "v0.2.0", "commit": "abc123"})


BASE = {
    "untouched.py": b"v1\n",
    "customized.md": b"title\n\nline a\n\nline b\n",
    "clashing.md": b"one\n",
    "deleted-here.yml": b"on: push\n",
    "dropped.md": b"old guide\n",
    "dropped-customized.md": b"old guide\n",
    "same-upstream.txt": b"same\n",
}
NEW = {
    "untouched.py": b"v2\n",
    "customized.md": b"title\n\nline a\n\nline b changed upstream\n",
    "clashing.md": b"two upstream\n",
    "deleted-here.yml": b"on: pull_request\n",
    "same-upstream.txt": b"same\n",
    "brand-new.py": b"new\n",
}
OURS = {
    "untouched.py": b"v1\n",
    "customized.md": b"title changed here\n\nline a\n\nline b\n",
    "clashing.md": b"two here\n",
    "dropped.md": b"old guide\n",
    "dropped-customized.md": b"our guide now\n",
    "same-upstream.txt": b"same\n",
}


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repository(OURS)
        self.addCleanup(self.repo.close)

    def run_update(self, write: bool = True) -> dict:
        outcome = stage.stage(manifest(NEW), NEW, self.repo.target, self.repo.staging, BASE, write=write)
        return {kind: paths for kind, paths in outcome.items() if paths}

    def test_each_file_takes_the_three_way_outcome(self):
        self.assertEqual(self.run_update(), {
            "added": ["brand-new.py"],
            "updated": ["untouched.py"],
            "merged": ["customized.md"],
            "conflict": ["clashing.md"],
            "missing": ["deleted-here.yml"],
            "removed": ["dropped.md"],
            "kept": ["dropped-customized.md"],
            "unchanged": ["same-upstream.txt"],
        })
        self.assertEqual(self.repo.read("untouched.py"), b"v2\n")
        self.assertEqual(self.repo.read("customized.md"), b"title changed here\n\nline a\n\nline b changed upstream\n")
        conflicted = self.repo.read("clashing.md")
        self.assertIn(b"<<<<<<< yours", conflicted)
        self.assertIn(b"two upstream", conflicted)
        self.assertIsNone(self.repo.read("dropped.md"))
        self.assertEqual(self.repo.read("dropped-customized.md"), b"our guide now\n")
        self.assertIsNone(self.repo.read("deleted-here.yml"))
        self.assertIn(b"+on: pull_request", (self.repo.staging / "deleted-here.yml.patch").read_bytes())

    def test_a_dry_run_changes_nothing(self):
        plan = self.run_update(write=False)
        self.assertEqual(plan["conflict"], ["clashing.md"])
        for path, data in OURS.items():
            self.assertEqual(self.repo.read(path), data, path)
        self.assertIsNone(self.repo.read("brand-new.py"))
        self.assertIsNone(self.repo.read(stage.VERSION_MARKER))

    def test_running_again_after_resolving_changes_nothing(self):
        self.run_update()
        (self.repo.target / "clashing.md").write_bytes(b"two upstream\n")
        again = stage.stage(manifest(NEW), NEW, self.repo.target, self.repo.staging, NEW)
        self.assertEqual({k: v for k, v in again.items() if v}, {"unchanged": ["brand-new.py", "clashing.md", "same-upstream.txt", "untouched.py"]})

    def test_base_detection_prefers_the_closest_release(self):
        older = {**BASE, "untouched.py": b"v0\n", "customized.md": b"something else entirely\n"}
        self.assertGreater(stage.match_score(BASE, self.repo.target), stage.match_score(older, self.repo.target))
        self.assertGreater(stage.match_score(BASE, self.repo.target), stage.match_score(NEW, self.repo.target))

    def test_writes_need_a_clean_git_checkout(self):
        self.assertIn("isn't a git repository", stage.dirty(self.repo.target))
        subprocess.run(["git", "init", "-q", str(self.repo.target)], check=True)
        self.assertIn("uncommitted changes", stage.dirty(self.repo.target))
        subprocess.run(["git", "-C", str(self.repo.target), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(self.repo.target), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                        "commit", "-qm", "base"], check=True)
        self.assertIsNone(stage.dirty(self.repo.target))

    def test_release_notes_since_the_base(self):
        changelog = "# Changelog\n\n## v0.3.0 - x\n* three\n\n## v0.2.0 - x\n* two\n\n## v0.1.0 - x\n* one\n"
        notes = stage.notes_since(changelog, "v0.1.0", "v0.3.0")
        self.assertIn("* three", notes)
        self.assertIn("* two", notes)
        self.assertNotIn("* one", notes)


if __name__ == "__main__":
    unittest.main()
