---
type: guide
status: stable
sources:
  - resource: README.md
  - resource: AGENTS.md
  - resource: CONTRIBUTING.md
  - resource: SECURITY.md
  - resource: skills/helicopter/references/modes.md
  - resource: skills/helicopter/references/operating.md
---
# Overview

Helicopter is a small policy layer around the normal GitHub pull request flow.
It is copied into the adopting repository; it is not a service or package that
runs a separate control plane. The repository's own GitHub settings, CI, and
human reviewers remain the enforcement boundary.

## The ramp

A pull request earns the next, more expensive step only after the cheaper step
passes:

1. **Admission:** `validate-metadata` checks the pull request contract, bot
   pull requests from forks, DCO sign-off when enabled, target branch, open-PR budget, and
   size limits. It reports actionable refusal codes; it does not judge whether
   the patch is correct.
2. **First review (optional):** after admission, `first-review` can run
   PR-Agent with the repository's `HELICOPTER_REVIEW_KEY`. The review is
   advisory and reads the pull request through the API.
3. **Queue:** `pr_queue.py` derives whose turn it is from the timeline and
   emits labels, notices, nudges, and an honest pause when maintainers have not
   had capacity.
4. **Human merge:** CODEOWNERS, independent project CI, branch protection, and
   the protected ruleset decide whether a human merges the change.

A push starts the ramp again. A successful admission is not approval, and an
automated review is not a substitute for human review.

## Components

- `scripts/validate_pr.py` — dependency-free metadata admission for one GitHub
  pull request event JSON file.
- `scripts/pr_queue.py` — stateless queue reconciliation through the GitHub API;
  labels and notices are outputs, never inputs.
- `scripts/configure_repository.py` — applies a selected repository mode,
  branch protection, labels, and security baseline through GitHub's API.
- `scripts/check_install.py` — read-only comparison of an adopting repository's
  files and live settings with Helicopter's definitions.
- `skills/helicopter/` — the companion agent skill for installing, updating,
  checking, and explaining an adoption. Its references are the detailed
  operating guides.
- `.github/workflows/contribution-intake.yml` and
  `.github/workflows/contribution-queue.yml` — privileged workflows that load
  scripts from the protected default branch and never execute contributor code.

Development-only files are intentionally separate from the adopter surface;
`AGENTS.md` lists the development tooling and tests that do not ship in a
release.

## Repository modes

Choose the mode that matches who maintains the repository:

| Mode | Admission exemption | Protected-branch review |
| --- | --- | --- |
| `solo` | Only the configured immutable maintainer ID on a same-repository branch | Zero required approvals |
| `contributor` | None; every contribution follows the contract | One CODEOWNER approval |
| `team` | Same-repository `OWNER`, `MEMBER`, or `COLLABORATOR` authors | One CODEOWNER approval after the latest push |

An unset or invalid mode fails closed to `contributor`. External contributors,
bots on forks, and fork pull requests follow the full contribution
path even in `solo` or `team` mode.

Read `skills/helicopter/references/modes.md` when changing mode or interpreting
trust exemptions, and `skills/helicopter/references/operating.md` when working
on permissions, queue timing, or incident response.

## Trust boundary

Privileged intake jobs use `pull_request_target`, `issue_comment`, or a
scheduled run so that workflow and script code comes from the protected default
branch. They read event metadata and GitHub API responses, but do not check out,
build, or execute the contributor head. Project builds and tests belong in a
separate `pull_request` workflow without secrets.

The optional review is the only job holding the model key. Job-scoped write
permissions let it post a review while queue jobs write labels and notices
without a secret. External Actions are pinned to full commit SHAs and the
PR-Agent image is pinned by digest. Changes to these controls should be owned by
`.github/CODEOWNERS` and reviewed as security-sensitive policy changes.

## What it cannot prove

Helicopter cannot prove that a signer understood the patch, that a contribution
is correct, safe, licensed, useful, or in scope, that a human-looking account
is not automated, or that maintainers have capacity. The queue makes missing
capacity visible; it cannot create capacity. Keep independent CI, dependency and
security checks, rulesets, CODEOWNERS, and human review in place.
