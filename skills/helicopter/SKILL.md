---
name: helicopter
description: Use this skill to install Helicopter's contribution governance in a GitHub repository, update an installed copy to the latest release, check that a repository is set up correctly, or explain and operate it. Covers the pull request admission check and its refusal codes, the optional first review, the whose-turn queue and its queue labels, maintainer modes (solo, contributor, team), branch protection and the security baseline, and adopting a repository that copied Helicopter before versions were recorded. Use it whenever a user mentions Helicopter, contribution governance or intake, pull request admission or queue labels, or updating governance files that came from grosspoetrysystems/helicopter.
license: MIT
compatibility: Needs git, Python 3.9+, the GitHub CLI (gh) signed in, and network access to github.com. Repository settings need an administrator.
metadata:
  repository: grosspoetrysystems/helicopter
---

# Helicopter

Helicopter's files are copied into a repository and then belong to it, so installing and updating are merges, not package upgrades. Every change goes through a pull request the maintainer merges. Never push to the default branch, merge, or change GitHub settings unless the maintainer says so.

## Start here

From the repository root (the script refuses to write into a working tree with uncommitted changes, so every change can be undone with git):

```sh
python3 scripts/stage.py --target . --dry-run
```

`scripts/stage.py` is in this skill's directory. It prints a JSON plan; its `mode` says what to do:

| `mode` | Meaning | Go to |
| --- | --- | --- |
| `install` | No Helicopter here yet | [Install](#install) |
| `update` | Behind the latest release. `base` is the installed release; `base_detected: true` means there was no version marker and the closest matching release was picked | [Update](#update) |
| `current` | Already on the latest release | [Check](#check) |

To explain how something works or to change settings, see [References](#references).

## Install

1. **Gather.** Ask only for what the repository doesn't show: the maintainer mode (`solo` for one maintainer, `contributor` for a maintainer-led project with outside contributions, `team` for several maintainers), the CODEOWNERS owners, the private security contact, and DCO (default) or CLA. For a new repository, create it first: `gh repo create OWNER/NAME --private --clone`.
2. **Stage.** `git switch -c helicopter-install`, then `python3 scripts/stage.py --target .`. Every file is checked against the release manifest; nothing is overwritten. Handle the plan's `files` as in [Plan outcomes](#plan-outcomes).
3. **Adapt.** Replace Helicopter's owners, contacts, and name in `.github/CODEOWNERS`, `SECURITY.md`, `.github/ISSUE_TEMPLATE/*`, `CODE_OF_CONDUCT.md`, and `CONTRIBUTING.md`. Add the project's dependency manifests, lockfiles, release paths, and security-sensitive code to CODEOWNERS. Put the project's builds and tests in their own `pull_request` workflow with no secrets.
4. **Register.** Add to `AGENTS.md` (create it if missing): `Contribution governance comes from Helicopter (.github/helicopter/version.json). Use the helicopter skill to update or check it: npx skills add grosspoetrysystems/helicopter`.
5. **Verify and open the pull request.** See [Check](#check), then one signed-off commit, `feat: adopt Helicopter vX.Y.Z`, and `gh pr create`.
6. **After the merge**, only when the maintainer says so: open one valid and one deliberately invalid draft pull request so `test-validator` and `validate-metadata` report once, then run `python3 scripts/configure_repository.py MODE` and the checker again. For a CLA, `gh variable set HELICOPTER_SIGNOFF --body off`. For the optional first review, the maintainer adds a `HELICOPTER_REVIEW_KEY` secret (an OpenRouter key with a credit limit).

## Update

1. `git switch -c helicopter-update-VERSION`, then `python3 scripts/stage.py --target .`. If a Dependabot pull request bumping `grosspoetrysystems/helicopter` started this, work on its branch instead: the update lands in that pull request.
2. Turn the plan into a task list before editing anything: one task per `merged`, `conflict`, `differs`, and `missing` file, and one per entry under `### Action required` in `release_notes` (each says exactly what to do).
3. Work the tasks as described in [Plan outcomes](#plan-outcomes).
4. Commit in this order, following the repository's commit convention, each signed off:
   1. `chore(helicopter): update to VERSION`: the `added`, `updated`, and `removed` files, `.github/helicopter/version.json`, `.github/helicopter/LICENSE`, and `.github/workflows/helicopter-release.yml` when the plan lists it. These are exactly the release's files, so this commit needs no review of its own.
   2. `chore(helicopter): merge VERSION into customized files`: every `merged`, resolved `conflict`, `differs`, and `missing` file. If they span unrelated areas (workflows, scripts, policy text), commit per area.
   3. One commit per Action required item that changes files.
5. [Check](#check), then `gh pr create`. In the body: `Closes #N` for an open "Helicopter VERSION is available" issue, base and new version, the release notes link, every merge decision you made, and a checklist of Action required items that need the maintainer (settings, secrets, variables), with the exact command for each.

When `base_detected` is true, say so in the pull request and name the release; the maintainer confirms it.

## Plan outcomes

- `added`, `updated`, `removed`, `unchanged`: done. Nothing to review.
- `merged`: a clean three-way merge of their customization and the release. Read the diff; a clean merge can still be wrong.
- `conflict`: written with `<<<<<<< yours` / `>>>>>>> release` markers. Keep the stronger control where they disagree; never drop the repository's own CI, required checks, or security policy.
- `differs`: the repository has its own file where Helicopter has one (install), or it isn't text. The release's copy is in `staging`; merge it by hand.
- `missing`: in the base but deleted or renamed here. `staging` has `PATH.patch`, the upstream change; apply it to the renamed file, or confirm the deletion with the maintainer.
- `kept`: Helicopter dropped the file, but it was customized here, so it stays. Ask whether it's still wanted.

Keep these exactly as they are when merging: the job names `test-validator` and `validate-metadata` (required checks use them), every `HELICOPTER_*` variable, the `queue:` label names, and the `<!-- helicopter:... -->` comment markers the queue uses to find its own comments.

## Check

```sh
python3 -m unittest discover -s tests
python3 scripts/check_install.py
```

Both live in the repository after install. Every file line must pass before the pull request. Settings lines can fail until the maintainer runs the configurator after merging. [references/checker.md](references/checker.md) gives the fix for every line.

## Gotchas

From real installs:

- **Renamed jobs or workflows.** If the repository renamed the admission workflow or its jobs, the checker still finds the workflow, but `configure_repository.py` would require the original check names, which never report, and block every merge. Don't run it; set required checks by hand.
- **Same-named files.** A repository's own `README.md`, `lefthook.yml`, `release.yml`, or `.changes/` is not Helicopter's. The checker tells them apart by content; don't delete them.
- **`workflow_run` and `issue_comment` workflows** are privileged. A checkout there must name the default branch or no ref at all (GitHub then checks out the default branch, or the chosen ref on a manual `workflow_dispatch` run). Don't pin a manually dispatched deploy to the default branch just to satisfy the checker.
- **Search lag.** Don't count pull requests with GitHub search in a check; it lags a just-opened pull request. List them instead.

## References

Load only the one the task needs:

- [references/modes.md](references/modes.md): choosing or changing the maintainer mode, what each mode's branch protection does, trust rules for exemptions, and the repository baseline.
- [references/queue.md](references/queue.md): what each `queue:` label means for a contributor and what to do next.
- [references/operating.md](references/operating.md): job permissions, the review ramp and first review, queue timings, hopper searches, and incident response.
- [references/checker.md](references/checker.md): every `check_install.py` line, what it checks, and its fix.

## Scripts

- `scripts/stage.py [--target .] [--version vX.Y.Z] [--base vX.Y.Z] [--dry-run]` (this skill): installs or updates from a verified release. JSON plan on stdout; exits 1 when it refuses (release older than v0.2.0, an archive that doesn't match its manifest, or uncommitted changes) and writes nothing in that case. Safe to run again.
- `scripts/check_install.py [--repo OWNER/REPO]` (the repository): read-only setup check; exits 1 on any failure.
- `scripts/configure_repository.py MODE [--dry-run] [--extra-check NAME]` (the repository): applies branch protection, mode variables, labels, and the baseline. Administrator only.
