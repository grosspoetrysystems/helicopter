---
okf_version: "0.2"
---
# Helicopter documentation

Helicopter is contribution governance for GitHub repositories: a metadata
admission check, an optional first review, a whose-turn queue, and a
configurator, copied into a repository as plain files and GitHub Actions
workflows. It has no server and no web application of its own; its "web"
surface is the GitHub pull request, driven by `.github/workflows/`.

This corpus documents the two surfaces an agent operates:

- [Overview](overview.md) — what Helicopter is, the admission ramp, the
  components, the trust boundary, modes, and what it cannot prove.
- [Command-line tools](commands.md) — the local Python scripts an agent or
  maintainer runs: validate, queue, configure, check, and the install/update
  stager.
- [Pull request workflow](pull-request-workflow.md) — the GitHub Actions flow
  that runs admission, the optional review, and the queue on each pull request
  (the GitHub "web" surface).
- [Install and update](install-and-update.md) — adopting Helicopter into a
  repository and updating an installed copy through the companion skill.
- [Failure modes and limits](failure-modes.md) — admission refusal codes,
  queue labels, known gotchas, and the boundaries Helicopter does not cross.

Authoritative maintainer and agent guides live in the companion skill at
`skills/helicopter/SKILL.md` and `skills/helicopter/references/`; this corpus
maps the surfaces and points into that material rather than copying it.
