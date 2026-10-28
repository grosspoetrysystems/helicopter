# Working on Helicopter

Helicopter is a contribution-governance template for GitHub repositories: an admission check (`scripts/validate_pr.py`), a first review (`.pr_agent.toml`), a whose-turn queue (`scripts/pr_queue.py`), and a configurator (`scripts/configure_repository.py`). Adopters copy it into their own repositories, so everything outside the development files below ships to them.

## Checks

- Install the hooks once: `lefthook install` (needs `actionlint`, `zizmor`, and `changie` on PATH).
- Tests: `python3 -m unittest discover -s tests`. Stdlib Python only; no new dependencies.
- Before pushing, the hooks run the tests, `actionlint`, `zizmor`, the workflow invariants (`scripts/dev_checks.py workflows`), and the changelog-fragment check. CI runs the same checks on every pull request.

## Changes

- One branch and one pull request per change. Never push to `main`.
- Commit subjects follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`, `chore:`, `perf:`, `build:`, `revert:`). Sign and sign off every commit: `git commit -S -s`.
- Every change to shipped files adds a changelog fragment: `changie new`. Pick the kind (`Added`, `Changed`, `Removed`, `Fixed`, `Security`, or `Action required`) and write one line for adopters. Use `Action required` when adopters must do something, and say exactly what.

## Trust boundary

- Pin every action to a full commit SHA, and every image to a digest.
- Jobs on privileged triggers (`pull_request_target`, `workflow_run`, `issue_comment`) never check out or run pull request code; they check out the default branch only. `scripts/dev_checks.py workflows` enforces this.
- Model output and contributor text are untrusted input. They never set priority, run commands, or skip review.
- Never commit keys or tokens.

## Agents in this repository

- Agents and bots never approve pull requests or count toward a required review.
- A push after a human approval needs a fresh human review.

## Releases

1. In a release pull request, run `changie batch auto && changie merge` and commit the result.
2. After it merges, tag the merge commit: `git tag -s vX.Y.Z && git push origin vX.Y.Z`.
3. `release.yml` publishes the GitHub release with the notes and `helicopter.json` (the version, commit, and a SHA-256 of every shipped file). The latest manifest is at `releases/latest/download/helicopter.json`.

Release tags can't be moved or deleted.

## Files adopters don't get

Helicopter's development tooling (`AGENTS.md`, `lefthook.yml`, `.changie.yaml`, `.changes/`, `CHANGELOG.md`, `scripts/dev_checks.py`, `scripts/release_manifest.py`, their tests, `.github/workflows/checks.yml`, `.github/workflows/release.yml`), its own `README.md` and header image, and the companion skill (`skills/helicopter/`, with `tests/test_stage.py`) stay out of releases: `NOT_SHIPPED` in `scripts/check_install.py` lists them. The skill installs and updates from a release's manifest files only, and the checker flags any of these in an adopter's copy. The other tests ship, because adopters' required check `test-validator` runs them.

Guides for maintainers and agents live only in the skill (`SKILL.md` and `references/`), not in shipped markdown. Keep `SKILL.md` under 500 lines and point to each reference with when to load it. When a shipped file changes how something works, update the matching reference in the same pull request.

