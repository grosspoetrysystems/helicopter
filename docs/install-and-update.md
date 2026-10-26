---
type: guide
status: stable
sources:
  - resource: README.md
  - resource: skills/helicopter/SKILL.md
  - resource: skills/helicopter/scripts/stage.py
  - resource: scripts/check_install.py
  - resource: scripts/configure_repository.py
  - resource: scripts/release_manifest.py
---
# Install and update

Helicopter is adopted as repository files, not installed as a runtime service.
The companion agent skill stages a release, compares it with the target, and
leaves repository changes for a maintainer to review.

## Prerequisites

The skill requires Git, Python 3.9 or newer, the GitHub CLI authenticated to the
target account, and network access to GitHub. Repository settings, rulesets, and
some security features require an administrator. Do not place keys in the
repository.

## First installation

From the target repository, ask the skill to install Helicopter in one of the
three modes: `solo`, `contributor`, or `team`. In the skill-runner context,
make a dry-run plan from the target repository root:

```sh
python3 scripts/stage.py --target . --dry-run
```

For a direct invocation from this source checkout, run from the Helicopter
source root and point `--target` at the adopter checkout:

```sh
python3 skills/helicopter/scripts/stage.py --target /path/to/adopter --dry-run
```

The real file is `skills/helicopter/scripts/stage.py` in this source
repository. The skill exposes it as `scripts/stage.py`; that path is
skill-provided, not an adopter file. It is never copied into an adopter's
installed release because the skill directory is excluded from releases.

For an install plan, create a branch, rerun the stage command without
`--dry-run`, then adapt owners, contacts, repository name, dependency and
security paths in CODEOWNERS, and the project's own build/test workflow. Add
the Helicopter registration line to `AGENTS.md`. Run the repository's checks and
`python3 scripts/check_install.py` before opening a pull request.

Do not run the configurator until `test-validator` and `validate-metadata` have
reported successfully. After a maintainer merges the installation, an
administrator can run:

```sh
python3 scripts/configure_repository.py MODE --repo OWNER/REPOSITORY
```

The configurator applies the mode, protection policy, labels, and baseline. Use
`--dry-run` to inspect its changes. Secrets, organization policy, and other
manual steps remain explicit rather than being guessed by the skill.

## Updating

Run the stage dry-run and read its JSON plan. For an update, turn every
`merged`, `conflict`, `differs`, `missing`, and release-note `Action required`
item into a review task. A clean merge is still a semantic change: preserve the
repository's CI, security policy, and required check names. Resolve conflicts
without dropping stronger controls, then run the checker and open the update
pull request for review.

The release manifest and the `.github/helicopter/version.json` marker the skill
writes into the adopter's copy identify the copied release. The skill updates
from releases rather than `main`; it does not commit, push, merge, change
settings, or deploy on the maintainer's behalf.

## Verify the resulting setup

```sh
python3 -m unittest discover -s tests
python3 scripts/check_install.py
```

The first command is the repository's validator test suite after adoption; the
second is the read-only setup check. Settings lines may remain actionable until
an administrator runs the configurator after merge. See
`skills/helicopter/references/checker.md` for the repair associated with each
checker line.
