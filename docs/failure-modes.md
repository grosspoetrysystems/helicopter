---
type: reference
status: stable
sources:
  - resource: scripts/validate_pr.py
  - resource: scripts/pr_queue.py
  - resource: scripts/check_install.py
  - resource: skills/helicopter/references/checker.md
  - resource: skills/helicopter/references/queue.md
  - resource: skills/helicopter/references/operating.md
---
# Failure modes and limits

Treat a refusal as a repair instruction, not as a verdict on the patch. The
validator checks metadata and shape; it does not establish correctness or
security.

## Admission refusal codes

`scripts/validate_pr.py` reports these actionable codes for an external,
non-draft pull request:

| Code | Repair |
| --- | --- |
| `REFUSE_TEMPLATE_INCOMPLETE` | Restore the `Change`, `Verification`, or `Risk` section from the template. |
| `REFUSE_CHANGE_EMPTY` | Describe the problem, smallest fix, and visible effect. |
| `REFUSE_VERIFICATION_EMPTY` | List commands or steps run and what they showed. |
| `REFUSE_RISK_UNCHECKED` | Check each changed risk area, or check `None of the above`, and explain it. |
| `REFUSE_SIGNOFF_MISSING` | Add a matching `Signed-off-by` to every non-merge commit, normally with `git rebase --signoff` and a force-push. |
| `REFUSE_OPEN_PR_LIMIT` | Convert another non-draft PR to draft or close it, then edit the description to retry. |
| `REFUSE_BASE_BRANCH` | Change the pull request base to the repository default branch. |
| `REFUSE_TOO_LARGE` | Split the change or ask a maintainer in an issue before resubmitting. |
| `REFUSE_BOT_UNAUTHORIZED` | Bots open pull requests from a branch of this repository, which needs write access; agents submit through a person's account. |
| `REFUSE_EVENT_INVALID` | Repair the event or commits JSON; this is an operational input error. |

The exact limits come from repository variables, with defaults of two open
non-draft PRs, 5,000 changed lines, and 300 changed files for contributors;
`0` disables an individual limit. Drafts wait for ready-for-review, and trusted
mode exemptions are narrowly defined in
`skills/helicopter/references/modes.md`.

## Queue is visible backpressure

Queue labels are derived from the timeline and may be repaired on the next
scheduled or comment-triggered run:

- `queue:awaiting-author` means the contributor must repair or respond;
- `queue:awaiting-reviewer` means the maintainer's turn is waiting;
- `queue:no-capacity` means the pause threshold passed; the PR stays open; and
- `queue:possibly-superseded` means a related PR merged and the maintainer
  should decide whether to close this one.

The queue never chooses reviewers, merges, or closes a pull request
automatically. Missing labels or GitHub API failures are operational failures;
inspect the workflow run and checker output rather than changing labels by
hand to hide the problem.

## Common setup gotchas

- Renaming `test-validator` or `validate-metadata` makes the configurator
  require checks that never report; set required checks by hand instead.
- A same-named `README.md`, `release.yml`, `lefthook.yml`, or `.changes/` may
  belong to the adopting repository; the checker distinguishes it by content.
  Do not delete it just to make a check green.
- Privileged `workflow_run` and `issue_comment` workflows must check out the
  default branch, not a pull request ref.
- GitHub search can lag a newly opened pull request; queue and admission use
  live API listings where the count matters.
- Settings and repository security features may be unavailable to automation;
  the configurator prints manual steps instead of inventing success.

## Hard limits

Helicopter does not prove signer comprehension, patch correctness, licensing,
scope, account humanity, maintainer capacity, or the truth of a contributor's
verification claims. It does not replace project CI, dependency/security
scanning, CODEOWNERS, rulesets, or human merge authority. When a workflow,
credential, dependency, or prompt-injection incident is suspected, do not run
untrusted contribution code: preserve run/actor/SHA evidence, revoke or rotate
exposed credentials, freeze affected merges or releases, and use private
security reporting.
