---
type: Reference
title: Install checker results
description: What each line of scripts/check_install.py checks and how to fix a failure.
---

# Install checker results

Run `python3 scripts/check_install.py` from the repository's checkout. It changes nothing. Each line reads `PASS`, `FAIL` (with its fix), or `ADMIN` (your token can't read the setting; ask an administrator to run it). It exits 1 when any line fails.

Most settings failures are fixed by running `python3 scripts/configure_repository.py MODE` again, which applies the same definitions the checker reads. Don't run it if you renamed the `test-validator` or `validate-metadata` jobs; fix those settings by hand.

## Settings

| Line | Checks | Fix |
| --- | --- | --- |
| mode variable | `HELICOPTER_MODE` is `solo`, `contributor`, or `team` | Run the configurator with your mode. |
| solo maintainer ID | In `solo` mode, `HELICOPTER_SOLO_MAINTAINER_ID` is a numeric user ID | Run the configurator as the maintainer. |
| branch protection | The default branch is protected | Run the configurator. |
| required checks | `test-validator` and `validate-metadata` are required, and branches must be up to date | Run the configurator; it keeps checks you already require. |
| administrators follow review rules | On in `team` mode only | Run the configurator. |
| reviews for MODE | Approvals, code-owner review, stale-review dismissal, and approval after the latest push, as the mode sets them | Run the configurator. |
| no force pushes or branch deletion | Both blocked | Run the configurator. |
| conversations resolved before merge | Required | Run the configurator. |
| workflow token read-only; Actions can't approve pull requests | Default token is read-only, and the repository setting that lets Actions approve is off | Run the configurator. |
| approval for first-time contributors' workflow runs | A maintainer approves a new contributor's first workflow run | Run the configurator. |
| queue labels | All four `queue:` labels exist | Run the configurator. |
| release tags can't move or be deleted | The `helicopter-release-tags` ruleset is active | Run the configurator. |
| secret scanning, push protection, Dependabot updates | All enabled | Run the configurator; private repositories may need a paid plan. |
| Dependabot alerts; private vulnerability reporting | Both enabled | Run the configurator. |
| sign-off on web commits | On, unless `HELICOPTER_SIGNOFF` is `off`; otherwise applied review suggestions fail the sign-off check | Run the configurator. |

## Files

| Line | Checks | Fix |
| --- | --- | --- |
| admission workflow | A workflow runs `validate_pr.py` on `pull_request_target`, under any file name | Restore `contribution-intake.yml`. |
| workflow trust boundary | Every action is pinned to a commit SHA or image digest; workflows on privileged triggers never reference or check out pull request code | Pin the action, or check out `${{ github.event.repository.default_branch }}`. |
| your own owners and contacts | CODEOWNERS, SECURITY.md, and the issue-template contact link name your project, not Helicopter | Replace them. |
| no Helicopter-only files | None of Helicopter's development tooling, README, or install guides | Delete the listed files. |
| Helicopter version marker | `.github/helicopter/version.json` names the release you installed | Install or update with the `install-helicopter` skill. |
| Helicopter license notice | `.github/helicopter/LICENSE` carries Helicopter's MIT license for the copied files | Copy it from the release. |
| files | The checkout is the repository named by `--repo` | Run from that repository's checkout. |
