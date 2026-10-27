# Changelog

All notable changes to Helicopter are recorded here. Each entry comes from a
changie fragment under `.changes/unreleased/`. See `AGENTS.md` for how to add one.



## v0.5.0 - 2026-10-27
### Changed
* Add upstream documentation and keep its Poolboy configuration, state, and publishing workflow out of adopter releases.
### Fixed
* The hourly queue no longer fails in repositories with issues turned off: the update notice is skipped there instead of stopping the sweep (since v0.3.0).
## v0.4.0 - 2026-10-26
### Action required
* Admission skips draft pull requests until they're marked ready for review, and refuses outside contributors' pull requests that target a branch other than the default (REFUSE_BASE_BRANCH) or change more than 5,000 lines or 300 files (REFUSE_TOO_LARGE). (**Action:** Do outside contributors target another branch? Change validate_shape in scripts/validate_pr.py. Set HELICOPTER_MAX_CHANGED_LINES or HELICOPTER_MAX_CHANGED_FILES to change the size limits (0 turns one off).)
## v0.3.0 - 2026-10-25
### Added
* The hourly queue opens one issue when a newer Helicopter release is out than the one in .github/helicopter/version.json, linking its release notes and counting its Action required steps. Close the issue to skip that release.
### Fixed
* The helicopter skill's update no longer stops on GitHub's API rate limit when finding the installed release, and adds Helicopter's license under .github/helicopter/ for copies installed before the version marker.
* check_install.py accepts a checkout with no ref in workflow_run and issue_comment workflows, where GitHub checks out the default branch anyway, so a deploy that can also be dispatched by hand keeps the operator's chosen ref. pull_request_target checkouts still have to name the default branch.
## v0.2.0 - 2026-10-25
### Added
* scripts/check_install.py checks a repository's Helicopter setup without changing anything: mode, branch protection, token defaults, labels, release-tag ruleset, security baseline, workflow trust boundary, your own owners, and no leftover development tooling. Each failure names its fix.
* A companion agent skill, helicopter (npx skills add grosspoetrysystems/helicopter), installs from a verified release or updates an installed copy: unchanged files are replaced, customized ones get a three-way merge, conflicts are left for review, and the release notes' Action required steps become a task list in one pull request. It records the release in .github/helicopter/version.json with Helicopter's license beside it; copies installed before the marker are matched to their release. check_install.py checks both.
### Changed
* Removing queue:possibly-superseded now dismisses it for good, and flagged pull requests no longer cost API calls on every hourly sweep.
* Releases no longer include Helicopter's README, MAINTAINERS.md, or docs/; their guidance moved into the helicopter skill's references, so adopters don't carry copies. An update removes them if you never changed them.
### Fixed
* The queue no longer fails when the queue labels are missing and no pull request needs one. Pull requests from bots in HELICOPTER_AUTOMATION_LOGINS are treated like the maintainer's own, skipped outside team mode.
* configure_repository.py keeps the status checks a branch already requires instead of replacing the list, so re-running it no longer drops your own CI or DCO checks.
### Action required
* Admission now refuses pull requests with unsigned commits, from bots not listed in HELICOPTER_AUTOMATION_LOGINS, and from outside contributors over the open pull request limit; CONTRIBUTING lists each rule next to its check. (**Action:** Using a CLA? Set the HELICOPTER_SIGNOFF repository variable to off. Set HELICOPTER_OPEN_PR_LIMIT to change the default limit of 2 (0 turns it off).)
## v0.1.0 - 2026-10-24
### Added
* Development checks for Helicopter itself: Lefthook hooks and a CI workflow for tests, actionlint, zizmor, workflow invariants, changelog fragments, and Conventional Commits.
* The review ramp: a first review by PR-Agent on DeepSeek V4.1 Flash (only when the HELICOPTER_REVIEW_KEY secret exists) and a whose-turn queue with nudges and pauses.
### Fixed
* scripts/configure_repository.py now runs on Python 3.9, the python3 that ships with macOS.
### Security
* A repository baseline: approval after the latest push in reviewed modes, read-only workflow tokens that can't approve pull requests, first-time-contributor workflow approval, Dependabot alerts and security updates, secret scanning with push protection, private vulnerability reporting, protected v* release tags, Dependabot for pinned actions with a 7-day cooldown, and wider CODEOWNERS.
### Action required
* The queue needs its labels. (**Action:** Run scripts/configure_repository.py again to create the queue: labels.)
* The pull request contract keeps only Change, Verification, and Risk: the per-PR attestations, the AI-origin choice, and the agent metadata and capabilities block are gone, and agreement is a one-time DCO sign-off. (**Action:** Replace .github/pull_request_template.md and the contract sections of CONTRIBUTING.md with Helicopter's.)
* The queue measures waits in hours (HELICOPTER_QUEUE_NUDGE_HOURS, default 168; HELICOPTER_QUEUE_PAUSE_HOURS, default 504), sweeps hourly, and in team mode also queues members' pull requests. (**Action:** If you set HELICOPTER_QUEUE_NUDGE_DAYS or HELICOPTER_QUEUE_PAUSE_DAYS, replace them with the _HOURS variables (multiply by 24).)
* The configurator applies the repository baseline, and maintainer-listed bots (HELICOPTER_AUTOMATION_LOGINS) pass admission on branches of the repository. (**Action:** Copy .github/dependabot.yml, then run scripts/configure_repository.py MODE --dry-run, review the output, and run it without --dry-run. If you already set HELICOPTER_AUTOMATION_LOGINS, add dependabot[bot].)
* The queue labels a pull request queue:possibly-superseded, with one comment, when another pull request for the same issue merged while it waited; nothing closes automatically. (**Action:** Run scripts/configure_repository.py again to create the queue:possibly-superseded label.)