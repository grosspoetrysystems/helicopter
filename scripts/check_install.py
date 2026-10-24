#!/usr/bin/env python3
"""Check that a repository is set up correctly for Helicopter. Read-only.

Run from the repository's checkout, as a user who can administer it:

    python3 scripts/check_install.py [--repo OWNER/REPOSITORY]

Settings are compared with what scripts/configure_repository.py sets for the repository's mode,
so running the configurator again fixes most failures. Exits 1 when anything fails.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from configure_repository import MODES, QUEUE_LABELS, REQUIRED_CHECKS, TAG_RULESET, protection

HELICOPTER = "grosspoetrysystems/helicopter"
PRIVILEGED_TRIGGERS = ("pull_request_target", "workflow_run", "issue_comment")
PINNED = re.compile(r"^(\./\S+|[\w.-]+/[\w./-]+@[0-9a-f]{40}|docker://\S+@sha256:[0-9a-f]{64})$")
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(\S+)")
PR_HEAD = re.compile(r"head\.sha|head\.ref|head_ref|refs/pull/|merge_commit_sha")
CHECKOUT = re.compile(r"uses:\s*actions/checkout@")
TRUSTED_REF = "ref: ${{ github.event.repository.default_branch }}"

# Helicopter's own development tooling: adopters don't get these, and the install removes them.
NOT_SHIPPED = (
    ".changes/",
    "AGENTS.md",
    "CHANGELOG.md",
    "lefthook.yml",
    ".changie.yaml",
    "scripts/dev_checks.py",
    "scripts/release_manifest.py",
    "tests/test_dev_checks.py",
    "tests/test_release_manifest.py",
    ".github/workflows/checks.yml",
    ".github/workflows/release.yml",
)

Fetch = Callable[[str], "tuple[int, Any]"]


@dataclass(frozen=True)
class Finding:
    status: str  # PASS, FAIL, or ADMIN (the token can't read it)
    item: str
    detail: str = ""


def workflow_problems(name: str, text: str) -> list[str]:
    """Return trust-boundary violations for one workflow file."""
    problems = []
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        match = USES.match(line)
        if match and not PINNED.match(match.group(1)):
            problems.append(f"{name}:{number}: action not pinned to a commit SHA or image digest: {match.group(1)}")

    triggers = re.search(r"^on:\s*\n((?:[ \t]+.*\n?)*)", text, re.M)
    on_block = triggers.group(1) if triggers else ""
    on_inline = re.search(r"^on:\s*(\S.*)$", text, re.M)
    on_text = on_block + (on_inline.group(1) if on_inline else "")
    if not any(re.search(rf"\b{trigger}\b", on_text) for trigger in PRIVILEGED_TRIGGERS):
        return problems

    for number, line in enumerate(lines, 1):
        if PR_HEAD.search(line):
            problems.append(f"{name}:{number}: privileged workflow references the pull request head")
        if CHECKOUT.search(line):
            step = []
            for following in lines[number:]:
                if re.match(r"^\s*-\s", following):
                    break
                step.append(following.strip())
            if TRUSTED_REF not in step:
                problems.append(f"{name}:{number}: privileged checkout must set `{TRUSTED_REF}`")
    return problems


def settings_findings(repository: str, fetch: Fetch) -> list[Finding]:
    """Compare the repository's live settings with what the configurator sets for its mode."""
    findings: list[Finding] = []

    def check(item: str, ok: bool, fix: str) -> None:
        findings.append(Finding("PASS", item) if ok else Finding("FAIL", item, fix))

    def read(endpoint: str, item: str) -> Any:
        status, body = fetch(endpoint)
        if status in (401, 403):
            findings.append(Finding("ADMIN", item, f"needs an administrator to read {endpoint}"))
            return None
        return body if status < 300 else {"status": status}

    variables = read(f"repos/{repository}/actions/variables?per_page=100", "mode variables")
    if variables is None:
        return findings
    values = {variable["name"]: variable["value"] for variable in variables.get("variables", [])}
    mode = values.get("HELICOPTER_MODE", "")
    configure = f"run `python3 scripts/configure_repository.py {mode if mode in MODES else 'MODE'} --repo {repository}`"
    check("mode variable", mode in MODES, f"HELICOPTER_MODE is {mode or 'unset'}; {configure}")
    if mode == "solo":
        check(
            "solo maintainer ID",
            re.fullmatch(r"[1-9][0-9]*", values.get("HELICOPTER_SOLO_MAINTAINER_ID", "")) is not None,
            f"HELICOPTER_SOLO_MAINTAINER_ID must be your numeric GitHub user ID; {configure}",
        )
    mode = mode if mode in MODES else "contributor"  # what the workflows fail closed to

    repo = read(f"repos/{repository}", "repository settings") or {}
    branch = repo.get("default_branch", "main")
    rules = read(f"repos/{repository}/branches/{branch}/protection", "branch protection")
    if rules is not None:
        if rules.get("status") == 404:
            check("branch protection", False, f"{branch} isn't protected; {configure}")
        else:
            want = protection(mode)
            checks = rules.get("required_status_checks") or {}
            check(
                "required checks",
                bool(checks.get("strict")) and set(REQUIRED_CHECKS) <= set(checks.get("contexts") or []),
                f"require up-to-date {', '.join(REQUIRED_CHECKS)}; {configure}",
            )
            check(
                "administrators follow review rules",
                bool((rules.get("enforce_admins") or {}).get("enabled")) == want["enforce_admins"],
                configure,
            )
            reviews, wanted = rules.get("required_pull_request_reviews") or {}, want["required_pull_request_reviews"]
            check(
                f"reviews for {mode} mode",
                reviews.get("required_approving_review_count", 0) >= wanted["required_approving_review_count"]
                and all(bool(reviews.get(key)) or not wanted[key] for key in
                        ("dismiss_stale_reviews", "require_code_owner_reviews", "require_last_push_approval")),
                f"approvals, code-owner review, and approval after the latest push; {configure}",
            )
            check(
                "no force pushes or branch deletion",
                not (rules.get("allow_force_pushes") or {}).get("enabled")
                and not (rules.get("allow_deletions") or {}).get("enabled"),
                configure,
            )
            check(
                "conversations resolved before merge",
                bool((rules.get("required_conversation_resolution") or {}).get("enabled")),
                configure,
            )

    actions = read(f"repos/{repository}/actions/permissions/workflow", "workflow token")
    if actions is not None:
        check(
            "workflow token read-only; Actions can't approve pull requests",
            actions.get("default_workflow_permissions") == "read" and actions.get("can_approve_pull_request_reviews") is False,
            configure,
        )
    approval = read(f"repos/{repository}/actions/permissions/fork-pr-contributor-approval", "first-time contributor approval")
    if approval is not None:
        check(
            "approval for first-time contributors' workflow runs",
            approval.get("approval_policy") in {"first_time_contributors", "all_external_contributors"},
            configure,
        )

    labels = read(f"repos/{repository}/labels?per_page=100", "queue labels")
    if labels is not None:
        missing = sorted(set(QUEUE_LABELS) - {label["name"] for label in labels})
        check("queue labels", not missing, f"missing {', '.join(missing)}; {configure}")

    rulesets = read(f"repos/{repository}/rulesets", "release-tag ruleset")
    if rulesets is not None:
        found = next((ruleset for ruleset in rulesets if ruleset.get("name") == TAG_RULESET), None)
        detail = read(f"repos/{repository}/rulesets/{found['id']}", "release-tag ruleset") if found else None
        check(
            "release tags can't move or be deleted",
            bool(detail) and detail.get("enforcement") == "active"
            and {"update", "deletion"} <= {rule["type"] for rule in detail.get("rules", [])},
            configure,
        )

    security = repo.get("security_and_analysis")
    if security is None:
        findings.append(Finding("ADMIN", "secret scanning and Dependabot updates", "needs an administrator to read"))
    else:
        off = [name for name in ("secret_scanning", "secret_scanning_push_protection", "dependabot_security_updates")
               if (security.get(name) or {}).get("status") != "enabled"]
        check("secret scanning, push protection, Dependabot updates", not off,
              f"{', '.join(off)} off; {configure} (some need a paid plan on private repositories)")
    status, _ = fetch(f"repos/{repository}/vulnerability-alerts")
    if status in (401, 403):
        findings.append(Finding("ADMIN", "Dependabot alerts", "needs an administrator to read"))
    else:
        check("Dependabot alerts", status == 204, configure)
    reporting = read(f"repos/{repository}/private-vulnerability-reporting", "private vulnerability reporting")
    if reporting is not None:
        check("private vulnerability reporting", bool(reporting.get("enabled")), configure)
    if values.get("HELICOPTER_SIGNOFF", "dco") != "off" and "web_commit_signoff_required" in repo:
        check("sign-off on web commits", bool(repo["web_commit_signoff_required"]),
              f"applied review suggestions would fail the sign-off check; {configure}")
    return findings


def file_findings(root: Path, repository: str) -> list[Finding]:
    """Check the checkout: safe workflows, the adopter's own names, no Helicopter development tooling."""
    findings: list[Finding] = []
    workflows = root / ".github/workflows"
    if not (workflows / "contribution-intake.yml").is_file():
        findings.append(Finding("FAIL", "Helicopter workflows", f"no {workflows / 'contribution-intake.yml'}; restore it, and run from the repository's checkout"))
    problems = [p for f in sorted(workflows.glob("*.y*ml")) for p in workflow_problems(f.name, f.read_text())]
    findings.append(Finding("FAIL", "workflow trust boundary", "; ".join(problems)) if problems
                    else Finding("PASS", "workflows pinned; privileged jobs never touch pull request code"))
    if repository.lower() == HELICOPTER:
        return findings

    leftovers = [name for name, marker in ((".github/CODEOWNERS", "@thekidnamedkd"), ("SECURITY.md", HELICOPTER))
                 if marker in ((root / name).read_text() if (root / name).is_file() else "")]
    findings.append(Finding("FAIL", "your own owners and contacts", f"replace Helicopter's in {', '.join(leftovers)}")
                    if leftovers else Finding("PASS", "your own owners and contacts"))
    tooling = [path for path in NOT_SHIPPED if (root / path).exists()]
    findings.append(Finding("FAIL", "no Helicopter development tooling", f"delete {', '.join(tooling)}")
                    if tooling else Finding("PASS", "no Helicopter development tooling"))
    return findings


def gh_fetch(endpoint: str) -> tuple[int, Any]:
    result = subprocess.run(["gh", "api", endpoint], check=False, capture_output=True, text=True)
    if result.returncode == 0:
        return (204, None) if not result.stdout.strip() else (200, json.loads(result.stdout))
    status = re.search(r"HTTP (\d{3})", result.stderr)
    if not status:
        raise SystemExit(result.stderr.strip())
    return int(status.group(1)), None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", help="OWNER/REPOSITORY; defaults to the current repository")
    args = parser.parse_args()
    repository = args.repo or subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()

    findings = settings_findings(repository, gh_fetch) + file_findings(Path("."), repository)
    for finding in findings:
        print(f"{finding.status:<5} {finding.item}" + (f": {finding.detail}" if finding.detail else ""))
    failed = sum(finding.status == "FAIL" for finding in findings)
    admin = sum(finding.status == "ADMIN" for finding in findings)
    print(f"\n{repository}: {failed} failing" + (f", {admin} need an administrator to check" if admin else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
