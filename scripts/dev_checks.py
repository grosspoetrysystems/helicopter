"""Helicopter's own development checks: workflow invariants, changelog fragments, commit subjects.

Run by Lefthook locally and by the `checks` workflow in CI. Not shipped to adopters.

    python3 scripts/dev_checks.py workflows
    python3 scripts/dev_checks.py changes BASE [HEAD]
    python3 scripts/dev_checks.py subject "feat: add the thing"   # or --file .git/COMMIT_EDITMSG
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from check_install import NOT_SHIPPED, workflow_problems

WORKFLOWS = Path(".github/workflows")
SUBJECT = re.compile(r"^(feat|fix|docs|refactor|test|ci|chore|perf|build|revert)(\([a-z0-9-]+\))?!?: \S.*$")

# Changes that need no changelog fragment: development tooling, plus tests (shipped, but not adopter-visible).
NO_NOTE_NEEDED = NOT_SHIPPED + ("tests/",)
FRAGMENTS = ".changes/unreleased/"


def missing_fragment(changed: list[str]) -> bool:
    """True when shipped files changed but no changelog fragment was added."""
    shipped = [path for path in changed if not path.startswith(NO_NOTE_NEEDED)]
    fragments = [path for path in changed if path.startswith(FRAGMENTS) and path.endswith(".yaml")]
    return bool(shipped) and not fragments


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("workflows")
    changes = commands.add_parser("changes")
    changes.add_argument("base")
    changes.add_argument("head", nargs="?", default="HEAD")
    subject = commands.add_parser("subject")
    subject.add_argument("text", nargs="?")
    subject.add_argument("--file")
    args = parser.parse_args()

    if args.command == "workflows":
        problems = [p for f in sorted(WORKFLOWS.glob("*.y*ml")) for p in workflow_problems(str(f), f.read_text())]
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0

    if args.command == "changes":
        # Only added fragments count, but any change to shipped files counts.
        changed = git("diff", "--name-only", f"{args.base}...{args.head}").splitlines()
        if missing_fragment(changed):
            print(
                "Shipped files changed without a changelog fragment. Add one with `changie new` "
                f"(it lands in {FRAGMENTS}); see AGENTS.md.",
                file=sys.stderr,
            )
            return 1
        return 0

    text = Path(args.file).read_text() if args.file else (args.text or "")
    first = text.splitlines()[0] if text.strip() else ""
    if first.startswith(("Merge ", "Revert \"", "fixup! ", "squash! ")) or SUBJECT.match(first):
        return 0
    print(
        f"Not a Conventional Commits subject: {first!r}. "
        "Use `type(scope): summary` with type feat, fix, docs, refactor, test, ci, chore, perf, build, or revert.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
