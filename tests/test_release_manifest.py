import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from release_manifest import action_required, shipped  # noqa: E402

NOTES = """## v0.2.0 - 2026-11-01
### Added
* A thing.
### Action required
* Rename a variable. (**Action:** do it.)
* Re-run the configurator. (**Action:** run it.)
### Fixed
* A bug.
"""


class ManifestTests(unittest.TestCase):
    def test_counts_only_action_required_entries(self):
        self.assertEqual(action_required(NOTES), 2)
        self.assertEqual(action_required("## v0.1.1\n### Fixed\n* A bug.\n"), 0)

    def test_development_files_are_not_shipped(self):
        files = ["scripts/pr_queue.py", "scripts/dev_checks.py", "scripts/release_manifest.py", "AGENTS.md",
                 ".changes/v0.1.0.md", "tests/test_ramp.py", ".github/workflows/release.yml", ".github/workflows/contribution-queue.yml"]
        files += ["tests/test_validate_pr.py", "tests/test_dev_checks.py"]
        # Adopters' required check test-validator runs the shipped tests.
        self.assertEqual(shipped(files), [".github/workflows/contribution-queue.yml", "scripts/pr_queue.py", "tests/test_ramp.py", "tests/test_validate_pr.py"])

    def test_poolboy_files_stay_out_of_release_but_adopter_policy_files_ship(self):
        files = [
            "docs/overview.md",
            ".poolboy/generated.json",
            "poolboy.toml",
            ".github/workflows/poolboy-docs.yml",
            ".github/workflows/contribution-policy-tests.yml",
            "SECURITY.md",
        ]
        self.assertEqual(
            shipped(files),
            [".github/workflows/contribution-policy-tests.yml", "SECURITY.md"],
        )


if __name__ == "__main__":
    unittest.main()
