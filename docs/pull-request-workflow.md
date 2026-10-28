---
type: workflow
status: stable
sources:
  - resource: .github/pull_request_template.md
  - resource: .github/workflows/contribution-intake.yml
  - resource: .github/workflows/contribution-queue.yml
  - resource: .github/workflows/contribution-policy-tests.yml
  - resource: scripts/validate_pr.py
  - resource: scripts/pr_queue.py
  - resource: scripts/risk_labels.py
  - resource: skills/helicopter/references/operating.md
---
# Pull request workflow

Helicopter's web-facing experience is GitHub's pull request UI. There is no
Helicopter web server. Contributors fill in the repository's pull request
template; Actions then perform bounded admission and queue work.

## Contributor contract

The template asks for:

- **Change:** the problem, smallest solution, visible effect, and an optional
  issue-closing reference;
- **Verification:** commands or steps run and their results, and what couldn't be run or tested; and
- **Risk:** every changed risk area checked, or `None of the above`, with details
  and mitigations.

The validator does not infer these claims. Missing or placeholder content is
refused with a repair code. Every non-merge commit must carry a matching
`Signed-off-by`, unless the repository explicitly sets `HELICOPTER_SIGNOFF=off`
for a CLA.

## Admission sequence

`.github/workflows/contribution-intake.yml` runs on pull request open, edit,
synchronize, reopen, ready-for-review, and conversion to draft. Its
`validate-metadata` job:

1. checks out only `scripts/` from the protected default branch;
2. reads commits and the author's open non-draft pull requests through the
   GitHub API (the live list is used rather than lagging search);
3. runs `scripts/validate_pr.py` with the configured mode, sign-off setting,
   open-PR limit, and size limits; and
4. stops before any expensive step when admission refuses the pull request.

A draft is reported as waiting until it is ready. Trusted maintainer paths and
bots on branches of this repository (which needs write access) receive a
metadata exemption, but human review still applies.

## Advisory risk labels

After `validate-metadata` passes, the separate `risk-labels` job checks out only
`scripts/` and `.gitattributes` from the protected default branch. It reads the
changed-file list through the GitHub API, never checks out or executes the
contributor head, and sets exactly the applicable `risk:` labels:
`risk:dependencies`, `risk:automation`, and `risk:generated`. It removes stale
`risk:` labels after a complete file listing, but retains them when GitHub's
file data is missing or capped at 3,000 because unknown absence is not a
negative finding. The job writes a small path-to-label table and the author's
ticked Risk boxes to the Actions summary. It is advisory: it does not comment,
refuse admission, or ask the author to change a box. Authentication and other
security-sensitive changes remain the author's Risk box because paths cannot
prove them.

## Optional first review

After `validate-metadata` passes, `first-review` runs only for a non-draft,
non-bot event and only when `HELICOPTER_REVIEW_KEY` is configured. PR-Agent is
pinned by image digest, reads the pull request through the API, and posts one
advisory review comment. It does not check out or execute contributor code, and
it cannot approve or move the queue.

## Queue and human review

The intake workflow's `queue` job checks out trusted default-branch scripts and
runs `pr_queue.py` with write permissions but no secret. The separate
`.github/workflows/contribution-queue.yml` repeats reconciliation on new PR
comments, hourly schedule ticks, and manual dispatch, so fork reviews and time
thresholds are noticed between pull request events.

The queue derives state from the timeline and uses these outputs:

- `queue:awaiting-author` while the contributor must repair or respond;
- `queue:awaiting-reviewer` while a maintainer's turn is waiting;
- `queue:no-capacity` after the configured pause threshold; and
- `queue:possibly-superseded` when a related pull request has merged.

The default nudge and pause thresholds are seven and twenty-one days. A pause
keeps the pull request open; nothing is merged or closed automatically. The
next step is independent project CI and human review through CODEOWNERS and the
protected branch ruleset.

## Security separation

Privileged intake and queue jobs never check out, build, or execute the
contributor head. Put project builds and tests in a separate `pull_request`
workflow with no secrets; this repository's
`contribution-policy-tests.yml` demonstrates the separate validator test path.
Keep `actions/checkout` and other Actions pinned to full commit SHAs and keep
job permissions narrow. Treat edits to workflows, policy files, and agent
instructions as security-sensitive changes.
