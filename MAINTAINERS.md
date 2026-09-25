# Maintainer setup and operations

Repository files express policy; GitHub settings enforce it. Complete this checklist before relying on the starter.

## Bootstrap

- [ ] Replace `PROJECT_NAME`, `PROJECT_DOMAIN`, `@ORG/MAINTAINERS`, and `@ORG/SECURITY`.
- [ ] Confirm DCO is the intended legal mechanism and configure its sign-off check, or replace it with the project's CLA/CA process.
- [ ] Decide which bot or GitHub App identities, if any, may interact with the project.
- [ ] Review the two-PR limit and issue-first categories in `CONTRIBUTING.md`.
- [ ] Create or replace the `needs-triage` and `automation-review` labels used by the issue forms.
- [ ] Test the pull request template and both acceptance/refusal paths of the intake workflow.
- [ ] Publish reachable private security and conduct contacts.

## GitHub settings

Configure a ruleset for the default branch:

- require pull requests and at least one human approval;
- require CODEOWNER approval for protected paths;
- dismiss stale approvals and require approval after the latest push;
- prevent the last pusher from supplying the final approval, where supported;
- require resolved review conversations;
- require `contribution-intake / validate-metadata` plus project CI;
- bind required checks to the expected GitHub App when supported;
- block force pushes and branch deletion;
- restrict bypass to a small emergency group; and
- require signed commits when practical.

For public repositories, set the concurrent non-draft PR limit for users without write access. Start at two unless maintainer capacity supports more; add trusted contributors to the bypass list deliberately.

Enable the security features appropriate to the project and plan: private vulnerability reporting, dependency graph/review, secret scanning and push protection, code scanning, and release attestations/SBOMs.

## Protect the policy plane

`.github/CODEOWNERS` covers this starter's workflows, validator, and governance files. Add the project's dependency manifests, lockfiles, authentication/security paths, release code, code generators, and agent instruction files.

The metadata workflow uses `pull_request_target` because that event loads its workflow from the protected base repository. Its safety depends on four invariants:

1. only event metadata and protected-base files are read;
2. the contributor head is never checked out or executed;
3. no secret is referenced; and
4. token permissions remain read-only.

Put builds and tests in a separate `pull_request` workflow on ephemeral GitHub-hosted runners. Pin every external action to a reviewed full commit SHA and set `persist-credentials: false` unless a job genuinely needs to push.

## Intake order

1. Check template, accountable human, origin, bot authorization, issue requirement, and PR budget.
2. Reject duplicates, out-of-scope work, and unreviewable size before expensive CI.
3. Route protected paths, dependencies, generated artifacts, and security-sensitive changes to owners.
4. Run independent tests and security checks without repository secrets.
5. Use automated or AI review only as advisory evidence.
6. Merge through the protected ruleset after human review.

Use one actionable response: one reason, one policy link, one repair path. Do not deploy several bots that repeat the same refusal.

## Risk and response

- **Routine:** Request a specific repair for missing fields, weak reproduction, or excessive scope.
- **Abuse:** Close duplicate, flooding, or unauthorized automation submissions, then apply PR or interaction limits.
- **Suspicious:** Quarantine dependency substitution, obfuscated files, reviewer prompt injection, or workflow escalation. Do not execute the contribution; involve security owners.
- **Incident:** Cancel runs, revoke identities, and freeze affected merges or releases after credential exposure, malicious workflow execution, a compromised bot or runner, or protected-branch compromise. Rotate possibly exposed credentials, preserve URLs, actor IDs, SHAs, run IDs, and logs, then rebuild from trusted state and use private disclosure.

Automation may triage or temporarily contain; a human must be able to reverse consequential moderation.

## Tune from evidence

Track maintainer minutes per accepted pull request, first-review latency, CI cost before triage, false refusal rate, major rewrite/revert rate, duplicate/spam rate, and repeat-contributor rate. Do not optimize for raw pull request count, generated lines, or bot comments.

Do not publish response-time promises until someone owns them. If you publish targets, call them service objectives rather than guarantees.
