#!/usr/bin/env python3
"""Stage a Helicopter release into a repository. Never overwrites a file.

    python3 stage.py [--version vX.Y.Z] [--target .]

Downloads the release manifest and the source archive at the manifest's commit, checks every shipped
file against the manifest's SHA-256, then:

- writes files the repository doesn't have yet;
- leaves files that are already identical;
- puts the release's copy of every file that differs in a staging directory, for you to merge by hand;
- writes the version marker, so later updates know which release this repository started from.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
import tempfile
import urllib.request
from pathlib import Path

REPOSITORY = "grosspoetrysystems/helicopter"
# Must match scripts/check_install.py; tests/test_stage.py checks that they agree.
VERSION_MARKER = ".github/helicopter/version.json"
INSTALL_PATHS = {"LICENSE": ".github/helicopter/LICENSE"}


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 (fixed https URLs)
        return response.read()


def release_files(manifest: dict, archive: bytes) -> dict[str, bytes]:
    """The manifest's files from the source archive, each checked against its hash."""
    wanted = manifest["files"]
    found: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for member in tar.getmembers():
            path = member.name.split("/", 1)[1] if "/" in member.name else ""
            if path in wanted and member.isfile():
                found[path] = tar.extractfile(member).read()
    problems = sorted(set(wanted) - set(found)) + sorted(
        path for path, data in found.items() if hashlib.sha256(data).hexdigest() != wanted[path]
    )
    if problems:
        raise SystemExit(f"The release archive doesn't match its manifest: {', '.join(problems)}. Nothing was written.")
    return found


def stage(manifest: dict, files: dict[str, bytes], target: Path, staging: Path) -> dict[str, list[str]]:
    """Write what's missing, stage what differs, record the version. Returns the paths by outcome."""
    outcome: dict[str, list[str]] = {"added": [], "unchanged": [], "differs": []}
    for path in sorted(files):
        destination = target / INSTALL_PATHS.get(path, path)
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(files[path])
            outcome["added"].append(str(destination.relative_to(target)))
        elif destination.read_bytes() == files[path]:
            outcome["unchanged"].append(str(destination.relative_to(target)))
        else:
            incoming = staging / INSTALL_PATHS.get(path, path)
            incoming.parent.mkdir(parents=True, exist_ok=True)
            incoming.write_bytes(files[path])
            outcome["differs"].append(str(destination.relative_to(target)))
    marker = target / VERSION_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"version": manifest["version"], "commit": manifest["commit"]}, indent=2) + "\n")
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", help="release tag, for example v0.2.0; default: the latest release")
    parser.add_argument("--target", type=Path, default=Path("."), help="the repository to install into")
    args = parser.parse_args()

    where = f"download/{args.version}" if args.version else "latest/download"
    manifest = json.loads(fetch(f"https://github.com/{REPOSITORY}/releases/{where}/helicopter.json"))
    files = release_files(manifest, fetch(f"https://github.com/{REPOSITORY}/archive/{manifest['commit']}.tar.gz"))
    staging = Path(tempfile.mkdtemp(prefix=f"helicopter-{manifest['version']}-"))
    outcome = stage(manifest, files, args.target.resolve(), staging)

    print(f"Helicopter {manifest['version']} ({manifest['commit'][:7]}); notes: {manifest['notes']}")
    for kind, paths in outcome.items():
        for path in paths:
            print(f"{kind:<9} {path}")
    if outcome["differs"]:
        print(f"\nMerge each file marked `differs` by hand; the release's copies are in {staging}")
    print(f"Wrote {VERSION_MARKER}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
