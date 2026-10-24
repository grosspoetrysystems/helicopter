import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "skills/install-helicopter/scripts"))

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


def manifest(files: dict[str, bytes]) -> dict:
    return {"version": "v0.2.0", "commit": "abc123", "files": {p: hashlib.sha256(d).hexdigest() for p, d in files.items()}}


RELEASE = {"CONTRIBUTING.md": b"rules\n", "scripts/validate_pr.py": b"code\n", "LICENSE": b"MIT\n"}


class StageTests(unittest.TestCase):
    def test_the_install_paths_match_the_checker(self):
        self.assertEqual(stage.VERSION_MARKER, check_install.VERSION_MARKER)
        self.assertEqual(stage.INSTALL_PATHS, check_install.INSTALL_PATHS)

    def test_archive_files_are_checked_against_the_manifest(self):
        self.assertEqual(stage.release_files(manifest(RELEASE), archive({**RELEASE, "README.md": b"x"})), RELEASE)
        tampered = archive({**RELEASE, "scripts/validate_pr.py": b"evil\n"})
        with self.assertRaisesRegex(SystemExit, "scripts/validate_pr.py"):
            stage.release_files(manifest(RELEASE), tampered)
        with self.assertRaisesRegex(SystemExit, "LICENSE"):
            stage.release_files(manifest(RELEASE), archive({p: d for p, d in RELEASE.items() if p != "LICENSE"}))

    def test_adds_missing_keeps_identical_and_stages_differences_without_overwriting(self):
        with tempfile.TemporaryDirectory() as target, tempfile.TemporaryDirectory() as staging:
            target, staging = Path(target), Path(staging)
            (target / "CONTRIBUTING.md").write_text("our own rules\n")
            (target / "scripts").mkdir()
            (target / "scripts/validate_pr.py").write_bytes(b"code\n")
            outcome = stage.stage(manifest(RELEASE), RELEASE, target, staging)

            self.assertEqual(outcome, {
                "added": [".github/helicopter/LICENSE"],
                "unchanged": ["scripts/validate_pr.py"],
                "differs": ["CONTRIBUTING.md"],
            })
            self.assertEqual((target / "CONTRIBUTING.md").read_text(), "our own rules\n")
            self.assertEqual((staging / "CONTRIBUTING.md").read_bytes(), b"rules\n")
            self.assertFalse((target / "LICENSE").exists())
            self.assertEqual(json.loads((target / stage.VERSION_MARKER).read_text()), {"version": "v0.2.0", "commit": "abc123"})


if __name__ == "__main__":
    unittest.main()
