---
name: install-helicopter
description: Installs Helicopter's contribution governance (admission check, first review, whose-turn queue, repository baseline) into a new or existing GitHub repository, adapts it to the project, and proves the result with Helicopter's install checker. Use when a maintainer asks to install, adopt, or set up Helicopter, or to add contribution governance, PR intake, or a review queue to a repository.
license: MIT
compatibility: Needs git, Python 3.9+, the GitHub CLI (gh) signed in, and network access to github.com. Repository settings need an administrator.
---

# Install Helicopter

Helicopter's files are copied into the repository and then belong to it. Install from a release, never from Helicopter's default branch, so the repository records exactly which version it started from.

You never push to the default branch, merge, or change GitHub settings without the maintainer saying so. You open a pull request; the maintainer merges it.

## 1. Gather

Confirm, asking only for what you can't find in the repository:

- **Repository:** new or existing. For existing, `git status --short` must be clean and `gh repo view` must name the right repository.
- **Maintainer mode:** `solo` (one maintainer), `contributor` (maintainer-led, outside contributions), or `team` (several maintainers; internal work is queued too). See `docs/maintainer-modes.md` after staging.
- **Owners:** the GitHub users or teams for CODEOWNERS.
- **Security contact:** GitHub private vulnerability reporting, or an address.
- **Contribution agreement:** DCO (the default; every commit is signed off) or a CLA.

For a new repository, create it empty and clone it: `gh repo create OWNER/NAME --private --clone` (or `--public`).

## 2. Stage the release

From the repository root, on a new branch (`git switch -c helicopter-install`), run this skill's script:

```sh
python3 scripts/stage.py --target .
```

If you only have this file, fetch the script first: `curl -fsSLO https://raw.githubusercontent.com/grosspoetrysystems/helicopter/main/skills/install-helicopter/scripts/stage.py`.

The script checks every file against the release manifest's hashes and never overwrites anything. It prints one line per file:

- `added`: the file was new and is now in place;
- `unchanged`: the repository already had this exact file;
- `differs`: the repository has its own file at that path. The release's copy is in the staging directory it prints.

It also writes `.github/helicopter/version.json` (the release) and `.github/helicopter/LICENSE` (Helicopter's MIT license, which the copied files need).

## 3. Merge and adapt

For every `differs` file, merge the release's copy into the repository's, keeping the stronger control wherever they disagree. Never delete the repository's own CI, required checks, or security policy. If the repository already has a contribution guide, merge Helicopter's "What's checked" table and Guidance into it rather than adding a second guide.

Then make the files the project's own:

- `.github/CODEOWNERS`: the owners from step 1, and add the project's dependency manifests, lockfiles, release paths, security-sensitive code, and generators.
- `SECURITY.md`, `.github/ISSUE_TEMPLATE/*`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `MAINTAINERS.md`: replace Helicopter's name, URLs, and contacts with the project's.
- `AGENTS.md` (create it if missing): add one line, `Contribution governance comes from Helicopter; see .github/helicopter/version.json. Update it with the install-helicopter skill.`
- Project builds and tests go in their own `pull_request` workflow with no secrets. Never add a checkout of pull request code, or a step that runs it, to `contribution-intake.yml` or `contribution-queue.yml`.

Keep these exactly as they are: the job names `test-validator` and `validate-metadata` (the configurator requires checks by those names, so renaming them blocks every merge), every `HELICOPTER_*` variable name, the `queue:` label names, and the `<!-- helicopter:... -->` comment markers the queue uses to find its own comments. Replace only owners, contacts, and the project's name in prose.

## 4. Verify and open the pull request

```sh
python3 -m unittest discover -s tests
python3 scripts/check_install.py
```

Before merge, the checker's settings lines may fail; that's expected until step 5. Every file line must pass: admission workflow, trust boundary, your own owners and contacts, no Helicopter-only files, version marker, license notice.

Commit with sign-off (`git commit -s`), push the branch, and open a pull request with `gh pr create`. Report to the maintainer: the files added and merged, every judgment call you made in a merge, the test and checker output, and the settings steps below.

## 5. After the maintainer merges

These change GitHub settings; run them only when the maintainer says so, as a repository administrator:

1. Open one valid and one deliberately invalid draft pull request, so the `test-validator` and `validate-metadata` checks have reported once.
2. `python3 scripts/configure_repository.py MODE`. It keeps the checks the branch already requires.
3. For a CLA: `gh variable set HELICOPTER_SIGNOFF --body off`, and add the CLA check.
4. Optional first review: add a `HELICOPTER_REVIEW_KEY` secret (an OpenRouter key with a credit limit).
5. `python3 scripts/check_install.py` until every line reads `PASS`. Lines marked `ADMIN` need an administrator's token to check.
