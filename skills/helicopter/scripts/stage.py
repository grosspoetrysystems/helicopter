#!/usr/bin/env python3
"""Install Helicopter from a release, or update an installed copy to a newer release.

    python3 scripts/stage.py --target .              # install, or update to the latest release
    python3 scripts/stage.py --target . --dry-run    # report what would change, write nothing
    python3 scripts/stage.py --version v0.2.0 --base v0.1.0

Prints a JSON plan on stdout; progress and errors go to stderr. Exit codes: 0 done (or nothing to do;
check "conflict" in the plan), 1 refused (release too old, an archive that doesn't match its manifest,
or a working tree with uncommitted changes),
2 bad arguments.

Downloads the release manifest and the source archive at the manifest's commit, and checks every file
against the manifest's SHA-256 before writing anything. The base is the release the repository has now:
read from .github/helicopter/version.json, or, for a copy installed before that marker existed, the
release whose files match the repository's most closely. Then, for every Helicopter file:

- added      new upstream, absent here: written
- updated    unchanged since the base: replaced with the release's copy
- merged     customized here and changed upstream: three-way merged cleanly (check it)
- conflict   three-way merge conflicted: written with conflict markers, resolve by hand
- differs    present here but not in the base, or not text: the release's copy is staged to merge by hand
- missing    in the base but deleted or renamed here: the upstream change is staged as a patch
- removed    dropped upstream and unchanged here: deleted
- kept       dropped upstream but customized here: left alone
- unchanged  already identical

Files Helicopter didn't change since the base are left alone however they look here.

It never overwrites a customized file except through a clean merge or one with conflict markers, reports
the release notes since the base, and writes the version marker. Running it again after a successful run
finds nothing to do.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

REPOSITORY = "grosspoetrysystems/helicopter"
# Must match scripts/check_install.py; tests/test_stage.py checks that they agree.
VERSION_MARKER = ".github/helicopter/version.json"
INSTALL_PATHS = {"LICENSE": ".github/helicopter/LICENSE"}
# A repository has Helicopter installed when it has these, however customized.
INSTALLED_SIGNS = ("scripts/validate_pr.py", "scripts/pr_queue.py")
# Older releases still listed Helicopter's own README and install guides, and had no install checker.
FIRST_SUPPORTED = (0, 2, 0)
OUTCOMES = ("added", "updated", "merged", "conflict", "differs", "missing", "removed", "kept", "unchanged")


def numbers(version: str) -> tuple[int, ...]:
    parts = tuple(int(part) for part in version.lstrip("v").split(".")[:3] if part.isdigit())
    return parts if len(parts) == 3 else ()


def supported(version: str) -> bool:
    return numbers(version) >= FIRST_SUPPORTED


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 (fixed https URLs)
        return response.read()


def archive_files(archive: bytes, wanted: set[str]) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for member in tar.getmembers():
            path = member.name.split("/", 1)[1] if "/" in member.name else ""
            if path in wanted and member.isfile():
                found[path] = tar.extractfile(member).read()
    return found


def release_files(manifest: dict, archive: bytes) -> dict[str, bytes]:
    """The manifest's files from the source archive, each checked against its hash."""
    wanted = manifest["files"]
    found = archive_files(archive, set(wanted))
    problems = sorted(set(wanted) - set(found)) + sorted(
        path for path, data in found.items() if hashlib.sha256(data).hexdigest() != wanted[path]
    )
    if problems:
        raise SystemExit(f"The release archive doesn't match its manifest: {', '.join(problems)}. Nothing was written.")
    return found


def match_score(files: dict[str, bytes], target: Path) -> tuple[int, float]:
    """How closely the repository matches a release: (files identical, summed text similarity)."""
    exact, similar = 0, 0.0
    for path, data in files.items():
        local = target / INSTALL_PATHS.get(path, path)
        if not local.is_file():
            continue
        ours = local.read_bytes()
        exact += ours == data
        similar += difflib.SequenceMatcher(None, ours.decode(errors="replace"), data.decode(errors="replace")).quick_ratio()
    return exact, similar


def merge(ours: bytes, base: bytes, theirs: bytes) -> tuple[int, bytes] | None:
    """git merge-file: (conflicts, merged bytes), or None when it can't merge (binary, error)."""
    if b"\0" in ours + base + theirs:
        return None
    with tempfile.TemporaryDirectory() as directory:
        paths = []
        for name, data in (("yours", ours), ("base", base), ("release", theirs)):
            path = Path(directory) / name
            path.write_bytes(data)
            paths.append(str(path))
        result = subprocess.run(
            ["git", "merge-file", "-p", "-L", "yours", "-L", "base", "-L", "release", *paths],
            capture_output=True, check=False,
        )
    return None if result.returncode < 0 else (result.returncode, result.stdout)


def patch(path: str, base: bytes, theirs: bytes) -> str:
    return "".join(difflib.unified_diff(
        base.decode(errors="replace").splitlines(keepends=True),
        theirs.decode(errors="replace").splitlines(keepends=True),
        f"a/{path}", f"b/{path}",
    ))


def stage(manifest: dict, files: dict[str, bytes], target: Path, staging: Path,
          base: dict[str, bytes] | None = None, write: bool = True) -> dict[str, list[str]]:
    """Bring the repository from `base` (empty for a new install) to `files`. Returns paths by outcome.

    With write=False nothing in `target` changes; staged copies and patches still go to `staging`.
    """
    base = base or {}
    outcome: dict[str, list[str]] = {kind: [] for kind in OUTCOMES}

    def stage_copy(name: str, data: bytes) -> None:
        (staging / name).parent.mkdir(parents=True, exist_ok=True)
        (staging / name).write_bytes(data)

    for path in sorted(set(files) | set(base)):
        name = INSTALL_PATHS.get(path, path)
        local = target / name
        ours = local.read_bytes() if local.is_file() else None
        old, new = base.get(path), files.get(path)
        if new is None:
            if ours is not None and ours == old:
                if write:
                    local.unlink()
                outcome["removed"].append(name)
            elif ours is not None:
                outcome["kept"].append(name)
            continue
        if old is not None and old == new and ours != new:
            continue  # unchanged upstream: whatever is here (customized, renamed, or deleted) stays as it is
        if ours is None:
            if old is None:
                if write:
                    local.parent.mkdir(parents=True, exist_ok=True)
                    local.write_bytes(new)
                outcome["added"].append(name)
            else:
                stage_copy(f"{name}.patch", patch(name, old, new).encode())
                outcome["missing"].append(name)
            continue
        if ours == new:
            outcome["unchanged"].append(name)
        elif old is not None and ours == old:
            if write:
                local.write_bytes(new)
            outcome["updated"].append(name)
        else:
            merged = merge(ours, old, new) if old is not None else None
            if merged is None:
                stage_copy(name, new)
                outcome["differs"].append(name)
            else:
                if write:
                    local.write_bytes(merged[1])
                outcome["conflict" if merged[0] else "merged"].append(name)

    if not write:
        return outcome
    marker = target / VERSION_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"version": manifest["version"], "commit": manifest["commit"]}, indent=2) + "\n")
    return outcome


def dirty(target: Path) -> str | None:
    """Why the repository can't be written safely, or None: merges and removals must be undoable with git."""
    status = subprocess.run(["git", "-C", str(target), "status", "--porcelain"], capture_output=True, text=True, check=False)
    if status.returncode:
        return f"{target} isn't a git repository; run from the repository's checkout. Nothing was written."
    if status.stdout.strip():
        return "The working tree has uncommitted changes; commit or stash them first, so the update can be undone. Nothing was written."
    return None


def notes_since(changelog: str, base: str, target: str) -> str:
    """The changelog sections after `base`, up to and including `target`."""
    sections = re.split(r"(?m)^(?=## v\d)", changelog)
    keep = [s for s in sections if (m := re.match(r"## (v[\d.]+)", s)) and numbers(base) < numbers(m.group(1)) <= numbers(target)]
    return "".join(keep).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", help="release to install, for example v0.2.0; default: the latest release")
    parser.add_argument("--base", help="release the repository has now; default: the marker, else the closest match")
    parser.add_argument("--target", type=Path, default=Path("."), help="the repository (default: .)")
    parser.add_argument("--dry-run", action="store_true", help="report the plan without changing the repository")
    args = parser.parse_args()
    target = args.target.resolve()

    def log(message: str) -> None:
        print(message, file=sys.stderr)

    def manifest_of(version: str | None) -> dict:
        where = f"download/{version}" if version else "latest/download"
        return json.loads(fetch(f"https://github.com/{REPOSITORY}/releases/{where}/helicopter.json"))

    release = manifest_of(args.version)
    if not supported(release["version"]):
        raise SystemExit(f"Helicopter {release['version']} predates this skill; use v0.2.0 or later. Nothing was written.")

    base_version = args.base
    if not base_version and (target / VERSION_MARKER).is_file():
        base_version = json.loads((target / VERSION_MARKER).read_text())["version"]
    base_manifest = manifest_of(base_version) if base_version else None
    detected = False
    if base_manifest is None and any((target / path).is_file() for path in INSTALLED_SIGNS):
        # Installed before the version marker existed: the closest release is the base. Customized copies
        # rarely match byte for byte, so text similarity breaks the tie.
        scores = []
        for tag in (r["tag_name"] for r in json.loads(fetch(f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100"))):
            candidate = manifest_of(tag)
            archive = fetch(f"https://github.com/{REPOSITORY}/archive/{candidate['commit']}.tar.gz")
            scores.append((match_score(release_files(candidate, archive), target), candidate))
        (exact, similar), base_manifest = max(scores, key=lambda pair: pair[0])
        detected = True
        log(f"No version marker; closest release is {base_manifest['version']} ({exact} files identical, similarity {similar:.1f}).")

    plan: dict = {
        "mode": "update" if base_manifest else "install",
        "base": base_manifest["version"] if base_manifest else None,
        "base_detected": detected,
        "version": release["version"],
        "notes": release["notes"],
        "dry_run": args.dry_run,
    }
    if base_manifest and numbers(base_manifest["version"]) >= numbers(release["version"]):
        log(f"Already on Helicopter {base_manifest['version']}; nothing to do.")
        print(json.dumps({**plan, "mode": "current"}, indent=2))
        return 0

    if not args.dry_run:
        refusal = dirty(target)
        if refusal:
            raise SystemExit(refusal)

    log(f"Fetching Helicopter {release['version']} ({release['commit'][:7]}) and checking it against its manifest.")
    archive = fetch(f"https://github.com/{REPOSITORY}/archive/{release['commit']}.tar.gz")
    files = release_files(release, archive)
    base = release_files(base_manifest, fetch(f"https://github.com/{REPOSITORY}/archive/{base_manifest['commit']}.tar.gz")) if base_manifest else {}
    staging = Path(tempfile.mkdtemp(prefix=f"helicopter-{release['version']}-"))
    outcome = stage(release, files, target, staging, base, write=not args.dry_run)

    plan.update(staging=str(staging), files={kind: paths for kind, paths in outcome.items() if paths})
    if base_manifest:
        changelog = archive_files(archive, {"CHANGELOG.md"}).get("CHANGELOG.md", b"").decode()
        plan["release_notes"] = notes_since(changelog, base_manifest["version"], release["version"])
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
