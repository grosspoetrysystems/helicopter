"""Build helicopter.json for a release: the version, commit, and a SHA-256 of every shipped file.

Adopters' update tooling compares these hashes with their own files: a match means the file is unmodified
and can be replaced; anything else was customized and gets a three-way merge. Matching hashes against
several releases' manifests also finds which version a repository started from.

    python3 scripts/release_manifest.py v0.1.0 --repo OWNER/REPOSITORY > helicopter.json

Run by .github/workflows/release.yml on a version tag. Not shipped to adopters.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from check_install import NOT_SHIPPED


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def shipped(paths: list[str]) -> list[str]:
    return sorted(path for path in paths if not path.startswith(NOT_SHIPPED))


def action_required(notes: str) -> int:
    """Count the entries under the release notes' "Action required" heading."""
    section = re.search(r"^### Action required\s*$(.*?)(?=^#|\Z)", notes, re.MULTILINE | re.DOTALL)
    return len(re.findall(r"^\* ", section.group(1), re.MULTILINE)) if section else 0


def manifest(version: str, repository: str) -> dict[str, object]:
    notes = Path(f".changes/{version}.md")
    if not notes.exists():
        raise SystemExit(f"{notes} is missing: run `changie batch {version} && changie merge` in a release pull request first.")
    files = shipped(git("ls-files", "-z").split("\0")[:-1])
    return {
        "version": version,
        "commit": git("rev-parse", "HEAD").strip(),
        "notes": f"https://github.com/{repository}/releases/tag/{version}",
        "action_required": action_required(notes.read_text()),
        "files": {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in files},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("version", help="the release tag, for example v0.1.0")
    parser.add_argument("--repo", required=True, help="OWNER/REPOSITORY, for the release notes link")
    args = parser.parse_args()
    print(json.dumps(manifest(args.version, args.repo), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
