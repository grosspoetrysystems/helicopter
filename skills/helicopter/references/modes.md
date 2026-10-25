# Maintainer operating modes

Contents: [Busy internal teams](#busy-internal-teams), [Configure or change mode](#configure-or-change-mode), [Repository baseline](#repository-baseline), [Trust decisions](#trust-decisions), [Shared protection policy](#shared-protection-policy), [Trusted intake](#trusted-intake), [Direct pushes and releases](#direct-pushes-and-releases), [Stacked pull requests](#stacked-pull-requests), [References](#references).

Helicopter separates trusted project work from external contribution intake. Choose one repository mode:

| Mode | Use when | Metadata exemption | Protected-branch reviews |
| --- | --- | --- | --- |
| `solo` | One human owns or maintains the project | The configured immutable user ID, on a same-repository branch | Zero required approvals |
| `contributor` | One or more maintainers primarily receive external contributions | None; every pull request follows the contribution contract | One CODEOWNER approval, given after the latest push |
| `team` | An internal organization team builds in the open and also accepts external contributions | Same-repository authors GitHub identifies as `OWNER`, `MEMBER`, or `COLLABORATOR` | One CODEOWNER approval after the latest push; administrators included |

Unset or invalid mode configuration fails closed to `contributor`.

## Busy internal teams

In `team` mode the queue also covers pull requests from members, because a team's pile-up is usually internal work waiting while people switch between tasks. The rules are the same in every mode: admission, the first review, and the turn clock work identically. Only the queue's scope and thresholds change.

- **Thresholds in hours.** Set `HELICOPTER_QUEUE_NUDGE_HOURS` and `HELICOPTER_QUEUE_PAUSE_HOURS` to the team's pace, for example 4 and 72.
- **Reviewer assignment stays with GitHub.** Helicopter doesn't pick reviewers. Use CODEOWNERS for who may review what, and GitHub's [team review assignment](https://docs.github.com/en/organizations/organizing-members-into-teams/managing-code-review-settings-for-your-team) (round robin or load balance) to spread requests. Nudges go to whoever GitHub requested.

## Configure or change mode

Authenticate an administrator, ensure the default branch exists, and run:

```sh
gh auth status
python3 scripts/configure_repository.py MODE --repo OWNER/REPOSITORY
```

Add `--dry-run` to print every change without making it. Checks the branch already requires are kept. Add `--extra-check NAME` (repeatable) to require another status check, but only one your `pull_request` workflows report on every pull request; a required check that never reports blocks every merge. If you renamed Helicopter's `test-validator` or `validate-metadata` jobs, don't run the configurator as is: it would require the original names, which never report. Replace `MODE` with `solo`, `contributor`, or `team`. The configurator:

1. protects the default branch;
2. requires up-to-date `test-validator` and `validate-metadata` checks;
3. blocks force pushes and branch deletion;
4. requires resolved conversations;
5. applies the review policy for the selected mode;
6. sets the repository-scoped `HELICOPTER_MODE` variable;
7. sets `HELICOPTER_SOLO_MAINTAINER_ID` to the authenticated user's immutable ID only in `solo` mode, and deletes it in other modes;
8. creates the `queue:` labels;
9. applies the repository baseline below, and protects release tags.

Run the configurator again to change modes, then `python3 scripts/check_install.py` from the repository's checkout to confirm every setting. Do not set Helicopter mode variables at organization scope: GitHub merges organization variables into the same `vars` context, which could affect every inheriting repository.

Required checks must have run successfully before making them required. During first installation, open valid and invalid draft pull requests before running the configurator.

## Repository baseline

Sound defaults for any repository, with or without agents. The configurator applies them in every mode; anything the plan doesn't allow (secret scanning on some private repositories, for example) is printed as a manual step instead of failing the run.

| Setting | Why |
| --- | --- |
| Approval after the latest push (`contributor`, `team`) | Whoever pushed last can't also approve. An agent or coworker pushing after a human approval needs a fresh review. |
| Administrators follow review rules (`team` only) | Several maintainers share the repository; `solo` and `contributor` keep admin merge for a lone maintainer's own work. |
| Workflow token read-only by default; workflows can't approve pull requests | A compromised or confused workflow can't write, and automation can never supply the required approval. |
| Approval for workflow runs from first-time contributors | A new account's pull request can't spend CI until a maintainer looks. |
| Dependabot alerts and security updates, secret scanning, push protection, private vulnerability reporting | Known-vulnerable dependencies and committed secrets surface early; reports arrive privately. |
| Web commits require sign-off | Commits made on GitHub, such as applied review suggestions, carry `Signed-off-by`, so admission's sign-off check accepts them. |
| `v*` tags can't move or be deleted | Each release's manifest stays tied to the exact files it describes. |
| `.github/dependabot.yml` | Keeps pinned action SHAs current, grouped into one weekly pull request. New versions wait 7 days (GitHub's default is 3); security updates are never delayed. Dependabot can't update `docker://` images, so bump the PR-Agent image by hand. |
| CODEOWNERS on `.github/`, `scripts/`, `tests/`, `.pr_agent.toml`, `AGENTS.md`, and policy files | Changes to automation and policy always reach a maintainer. |

**Authorized automation.** Bots listed in `HELICOPTER_AUTOMATION_LOGINS` pass admission on branches of this repository without the pull request template; human review still applies. The queue treats their pull requests like the maintainer's own: skipped in `solo` and `contributor` modes, queued in `team` mode. The configurator sets it to `dependabot[bot]` when it's unset; if you already set it, add `dependabot[bot]` yourself.

**Admission settings.** `HELICOPTER_SIGNOFF` (default `dco`; `off` for projects using a CLA) controls the sign-off check. `HELICOPTER_OPEN_PR_LIMIT` (default 2; `0` turns it off) caps open non-draft pull requests for contributors without write access. `HELICOPTER_MAX_CHANGED_LINES` (default 5000) and `HELICOPTER_MAX_CHANGED_FILES` (default 300; `0` turns either off) cap their size, and their pull requests must target the default branch. Drafts skip admission until they're marked ready for review.

## Trust decisions

### Solo

The exemption applies only when:

1. `HELICOPTER_SOLO_MAINTAINER_ID` is a positive decimal GitHub user ID;
2. the pull-request author and event sender are that user;
3. the author, sender, and repository owner are human users for a personal repository, or the repository belongs to an organization;
4. the event repository and pull-request base and head repositories have the same immutable repository ID.

Other users, bots, and forks follow the external contribution contract.

### Contributor

Nobody bypasses contribution metadata. This is the conservative mode for a maintainer-led open source project. External contributors cannot merge their own work; protected paths require CODEOWNER review.

Repository administrators retain emergency bypass because branch protection is not enforced for administrators. Use that authority deliberately.

### Team

GitHub's server-supplied `author_association` identifies trusted repository relationships. Helicopter accepts the internal path only when:

1. the author association is `OWNER`, `MEMBER`, or `COLLABORATOR`;
2. the author and event sender are the same human user;
3. the pull request uses a branch in the governed repository, not a fork.

The same-repository requirement matters: organization membership alone does not grant the exemption. An internal coworker using a fork follows the external path. A collaborator trusted with repository write access is treated as internal even if they are not an employee.

External contributors, bots, and fork pull requests always follow the full contribution contract.

## Shared protection policy

All modes:

- require the exact `test-validator` and `validate-metadata` check contexts;
- require branches to be up to date;
- require resolved review conversations;
- block force pushes and branch deletion;
- leave administrator enforcement disabled for emergency recovery;
- keep production deploy and release triggers explicit.

`solo` deliberately requires no approval because no second reviewer exists. `contributor` requires one approval but does not require approval after the latest push, allowing a maintainer to complete review after contributor updates. `team` requires approval after the latest push so one coworker cannot both supply the final update and final approval.

Check the effective settings, including branch protection, against the mode:

```sh
python3 scripts/check_install.py --repo OWNER/REPOSITORY
```

Repository rulesets and organization rulesets may add stricter controls:

```sh
gh api repos/OWNER/REPOSITORY/rulesets
gh api repos/OWNER/REPOSITORY/rules/branches/BRANCH
```

## Trusted intake

The intake workflow uses `pull_request_target` and loads its validator, review rules (`.pr_agent.toml`), and queue script from `github.event.repository.default_branch`. No job checks out or executes pull-request code; per-job permissions and the one optional secret are listed in [Protect the policy plane](operating.md#protect-the-policy-plane). The mode variable is read at run time, but workflow changes must reach the protected default branch before the new behavior exists.

The exemption returns success before parsing the pull-request body. It does not fill in or invent the Change, Verification, or Risk sections. Project builds and tests remain in an unprivileged `pull_request` workflow.

## Direct pushes and releases

A direct administrator push is appropriate only when an administrator has reviewed a small change locally and accepts that required checks run after it reaches the default branch. This is emergency or solo-maintainer authority, not proof that checks ran before landing.

Do not attach production publication to every default-branch push merely because administrators can bypass protection:

```text
push or merge to main  -> CI only
explicit site deploy   -> production site/landing publication
version tag or release -> CLI/package publication
```

## Stacked pull requests

GitHub can identify dependent pull requests as a stack. The normal GraphQL merge mutation may require the asynchronous REST merge endpoint:

```text
PUT /repos/OWNER/REPOSITORY/pulls/NUMBER/merge-async
GET /repos/OWNER/REPOSITORY/pulls/NUMBER/merge-async/UUID
```

A `202` only enqueues the merge. Poll until the result is `merged` or `failed`. The async endpoint has no administrator-override parameter, so required checks still apply.

## References

- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [About CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [REST API endpoints for branch protection](https://docs.github.com/en/rest/branches/branch-protection)
- [REST API endpoints for repository variables](https://docs.github.com/en/rest/actions/variables)
