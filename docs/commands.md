---
type: reference
status: stable
sources:
  - resource: scripts/validate_pr.py
  - resource: scripts/risk_labels.py
  - resource: scripts/pr_queue.py
  - resource: scripts/configure_repository.py
  - resource: scripts/check_install.py
  - resource: scripts/dev_checks.py
  - resource: scripts/release_manifest.py
  - resource: skills/helicopter/scripts/stage.py
  - resource: skills/helicopter/SKILL.md
---
# Command-line tools

The scripts are dependency-free Python where possible and operate on a GitHub
repository through the GitHub CLI or API. Run them from the repository root in
the environment described by the skill; do not treat a successful command as a
substitute for human review.

## Admission validator

```sh
python3 scripts/validate_pr.py EVENT_JSON \
  --mode solo|contributor|team \
  --solo-maintainer-id ID \
  --commits COMMITS_JSON \
  --open-prs N \
  --open-pr-limit N \
  --max-changed-lines N \
  --max-changed-files N
```

`EVENT_JSON` is the pull request event payload. `--commits` enables the
`Signed-off-by` check; the workflow omits it when `HELICOPTER_SIGNOFF=off` for
a CLA. The validator accepts drafts without admission until they are marked
ready. For an external contributor it checks the required `Change`,
`Verification`, and `Risk` sections, sign-off, bot pull requests from forks, target
branch, open non-draft PR count, and changed-file/line limits. Exit 1 is a
policy refusal; invalid event or commit JSON is an operational error (exit 2).

## Queue reconciliation

```sh
python3 scripts/pr_queue.py [--pr NUMBER] [--dry-run]
```

Without `--pr`, the queue reconciles every open pull request. With `--pr`, it
reconciles one. `--dry-run` prints writes rather than making them. The script
uses the GitHub API and `GITHUB_REPOSITORY`/`GITHUB_TOKEN`; it derives turn and
clock state from the timeline, so labels are outputs rather than caller-supplied
state.

## Advisory risk labels

```sh
GITHUB_REPOSITORY=OWNER/REPOSITORY GITHUB_TOKEN=TOKEN \
  python3 scripts/risk_labels.py --pr NUMBER [--dry-run]
```

The script reads changed paths from GitHub and `.gitattributes` from the trusted
default branch, then sets the applicable `risk:` labels and removes stale
`risk:` labels after a complete listing. `--dry-run` prints API writes instead
of applying them. Missing or capped file data is unknown: existing risk labels
are retained and the summary says the comparison may be incomplete. The
workflow writes that summary to `GITHUB_STEP_SUMMARY`; a local run prints it.

## Repository configuration and checking

```sh
python3 scripts/configure_repository.py MODE [--repo OWNER/REPOSITORY] \
  [--dry-run] [--extra-check NAME]
python3 scripts/check_install.py [--repo OWNER/REPOSITORY]
```

`MODE` is `solo`, `contributor`, or `team`. The configurator applies branch
protection, required checks, queue and advisory risk labels, mode variables, and
the permitted security baseline; it needs an administrator and can print manual
steps where GitHub does not permit automation. `--dry-run` makes it report
changes without applying them. `--extra-check` is repeatable, but only require
checks that run on every pull request. The checker is read-only and exits 1 for
any failure.

Run the checker again after configuration. If the repository renamed
`test-validator` or `validate-metadata`, do not run the configurator unchanged:
its required check names would never report.

## Skill staging

The companion skill starts with a plan. When invoking the script from this
source checkout, run it from the Helicopter source root and point `--target` at
the adopter checkout:

```sh
python3 skills/helicopter/scripts/stage.py --target /path/to/adopter --dry-run
```

When the companion skill runs against an adopter, its resource is exposed as
`scripts/stage.py`; run that command from the adopter's repository root:

```sh
python3 scripts/stage.py --target . --dry-run
```

The latter path is skill-provided, not a root-level script: `skills/helicopter/`
is excluded from releases, so an installed release has no `scripts/stage.py`.
The parser accepts `--version`, `--base`, `--target` (default `.`), and
`--dry-run`, resolving the target before reading its marker. A non-dry run
writes manifest files below `<target>` (mapping `LICENSE` to
`<target>/.github/helicopter/LICENSE`) and writes
`<target>/.github/helicopter/version.json`; dry runs leave the target unchanged.
Staged copies and patches go to the temporary `staging` path reported in the
JSON plan. The plan reports `install`, `update`, or `current`.
It refuses to write when the target has uncommitted changes, and it never
silently overwrites customized files. See [Install and update](install-and-update.md).

## Development checks

These are Helicopter's own development tools, not adopter commands:

```sh
python3 scripts/dev_checks.py workflows
python3 scripts/dev_checks.py changes BASE [HEAD]
python3 scripts/dev_checks.py subject TEXT
python3 scripts/release_manifest.py vX.Y.Z --repo OWNER/REPOSITORY
```

`dev_checks.py` validates workflow invariants, changelog fragments, and
Conventional Commit subjects. `release_manifest.py` prints the manifest for a
release tag. `AGENTS.md` lists the development-only files excluded from an
adopter release.
