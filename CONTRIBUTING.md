# Contributing to Helicopter

Helicopter welcomes useful, reviewable work however it was produced.

## Your agreement

You agree once, not on every pull request: sign off your commits under the [Developer Certificate of Origin](#legal), which certifies you have the right to submit the change. Pull requests themselves carry no declarations; reviewers judge the change, its verification, and its risk.

## AI and agent use

You don't need to declare how a change was produced.

A project adopting Helicopter can require disclosure by setting the repository variable `HELICOPTER_REQUIRE_DISCLOSURE` to `true` and adding a `## Disclosure` section to its pull request template. That section then must link a verifiable record, such as an [Agent Trace](https://agent-trace.dev/) file, or describe material AI or agent involvement, or say `None`. Never publish raw transcripts that may contain secrets, personal data, or restricted source material.

An agent must not:

- impersonate a person or conceal material automation;
- approve or merge its own contribution;
- bypass required checks or reviews;
- change policy or security controls merely to make its own work pass;
- use repository or deployment secrets in untrusted contribution CI;
- post substantive answers as though they were the accountable human's judgment; or
- flood Helicopter with speculative, duplicate, or unrelated submissions.

Maintainers moderate observable behavior and policy violations, not guesses that writing “looks AI-generated.”

## Before implementation

Open or reference an accepted issue before starting:

- a feature or public API change;
- a cross-cutting refactor;
- a dependency addition or replacement;
- authentication, authorization, or security-sensitive work; or
- a significant build, workflow, release, or policy change.

Small bug fixes, documentation corrections, and focused maintenance may skip issue-first review unless a maintainer says otherwise.

Unapproved bots and autonomous agents must not open issues, pull requests, reviews, or comments. Their accountable operator must request authorization with the **Automation authorization** issue form before they interact with Helicopter.

## Pull request contract

The pull request template has three required sections:

- **Change:** the problem, the smallest solution, and its user-visible effect; link an accepted issue when required.
- **Verification:** the commands or steps you ran and what they showed, or why verification doesn't apply.
- **Risk:** check every area the change touches (dependencies, security, workflows, generated content), or `None of the above`.

Each pull request should solve one coherent problem. If a section is missing or empty, the admission check names it and says how to fix it.

Use a draft pull request while work is incomplete. Maintainers may ask you to split unrelated, generated, mechanical, or otherwise unreviewable changes. Passing CI does not guarantee acceptance.

When you have addressed review, push your changes and reply, or press **Re-request review**. Either one hands the pull request back to a maintainer. Labels show whose turn it is: `queue:awaiting-author` is yours, `queue:awaiting-reviewer` is ours. An automated review may comment on your change first.

Contributors without write access may have at most **two non-draft pull requests** open at once unless a maintainer grants an exception.

## Review

Helicopter independently reruns relevant checks. Contributor and agent reports are useful context, not authoritative evidence. AI review is advisory and cannot replace required human approval.

Changes to workflows, security, authentication, dependencies, release machinery, contribution policy, or agent instructions require the owners named in `.github/CODEOWNERS`.

## Legal

Helicopter uses [Developer Certificate of Origin 1.1](https://developercertificate.org/). Sign off every commit:

```text
Signed-off-by: Your Name <your.email@example.com>
```

A person or authorized organization, not an AI system, makes that certification. A project adopting Helicopter can use a contributor license agreement (CLA) instead: replace this section with the CLA's terms and configure the CLA check in place of the DCO check.

Maintainers also sign their commits (`git commit -S`); outside contributors don't have to.

## Security and conduct

Report vulnerabilities privately as described in `SECURITY.md`. Follow `CODE_OF_CONDUCT.md` in all project spaces.
