# Agentic OSS Starter

A small, copyable policy and intake pack for open source repositories accepting human, AI-assisted, and agent-authored contributions.

Agents are untrusted, high-throughput automation acting for an accountable human. Keep submission and refusal cheap, and keep merge authority with people.

Passing CI makes a contribution reviewable. It does not prove the change is correct.

## Included

- `CONTRIBUTING.md`: one contribution contract for humans and agents.
- `.github/pull_request_template.md`: accountable owner, evidence, risk, and agent provenance.
- `.github/workflows/contribution-intake.yml`: metadata-only admission using policy code from the protected base commit.
- `scripts/validate_pr.py`: dependency-free validator with actionable refusal codes.
- `.github/CODEOWNERS` and `MAINTAINERS.md`: settings Git cannot enforce for you.
- `SECURITY.md`, `CODE_OF_CONDUCT.md`, and focused issue forms.

Add an agent framework, AI reviewer, provenance database, transcript storage, or policy DSL only when a real workflow needs it.

## Adopt it

1. Copy the files you need into the target repository. Review before overwriting existing community files.
2. Replace every `PROJECT_NAME`, `PROJECT_DOMAIN`, `@ORG/MAINTAINERS`, and `@ORG/SECURITY` placeholder.
3. Read `CONTRIBUTING.md`; change the DCO, issue-first, bot, and open-PR policies to match the project.
4. Run:

   ```sh
   python3 tests/test_validate_pr.py
   ```

5. Complete the GitHub settings in `MAINTAINERS.md`. The files alone do not create branch protection, PR limits, private vulnerability reporting, or security scanning.
6. Test one valid and one deliberately invalid draft PR before making `contribution-intake / validate-metadata` required.

The default open-PR budget is two non-draft PRs for contributors without write access. That is a starting point, not an industry norm; tune it from maintainer load and false refusals.

## Trust boundary

`contribution-intake.yml` uses `pull_request_target` only to read event metadata. It checks out the pull request's **base SHA**, never the contributor head, grants only `contents: read`, persists no credentials, and executes no contributor code. Do not add a head checkout, build, test, or PR-controlled action to that workflow.

Project tests belong in a separate `pull_request` workflow on an ephemeral hosted runner with no secrets and minimum token permissions.

## What automation cannot verify

The validator can establish that required declarations are present and internally consistent. It cannot prove that:

- the named person reviewed or understands the patch;
- an agent's capability or provenance claims are truthful;
- the base SHA was protected when the run started;
- the contribution is correct, safe, licensed, useful, or in scope;
- a bot identity is authorized; or
- the project has reviewer capacity.

Rulesets, CODEOWNERS, independent CI, dependency/security checks, and human review remain the enforcement boundary.

## Research basis

This pack is a smaller alternative to the generated starter in the supplied 2026 research. Its primary sources include:

- [GitHub Actions secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use): least-privilege tokens, immutable action SHAs, protected workflows, and no privileged execution of untrusted code.
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets): layered merge, review, and status-check controls.
- [GitHub interaction and pull-request limits](https://docs.github.com/en/communities/moderating-comments-and-conversations/limiting-interactions-in-your-repository): platform backpressure for public repositories.
- [OpenSSF's AI coding-assistant guidance](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions): developer responsibility and normal engineering controls still apply.
- [OpenSSF's OSS-CRS review](https://openssf.org/blog/2026/04/02/from-aixcc-to-openssf-welcoming-oss-crs-to-advance-ai-driven-open-source-security/): automated validation did not establish semantic correctness for many reviewed AI patches.
- [Rust's LLM usage policy](https://forge.rust-lang.org/policies/llm-usage.html): AI review is not a substitute for required human review.
- [Developer Certificate of Origin 1.1](https://developercertificate.org/): the human or organization, not a model, makes the legal certification.

## License

MIT. Adopted projects keep their own project license and contribution terms.
