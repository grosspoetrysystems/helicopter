# Add Helicopter to an existing repository

## Requirements

- [Git](https://git-scm.com/downloads)
- Python 3.10 or newer
- [GitHub CLI](https://github.com/cli/cli#installation)
- Write access to the repository; administrator access for GitHub settings

Start from a clean working tree and confirm the target repository and account:

```sh
git status --short
gh repo view
gh auth status
```

## Agent prompt

Open the repository in your coding agent and paste:

```text
Integrate the contribution controls from
https://github.com/grosspoetrysystems/helicopter into this repository.

Maintainer mode: <SOLO_OR_MULTI>

Inspect the existing contribution, security, conduct, ownership, issue,
pull-request, and CI files before editing. Preserve stronger existing controls
and merge into existing files instead of creating duplicate policies.

Adapt the imported files to this repository's maintainers, contribution
agreement, private security route, labels, required checks, dependencies,
lockfiles, release paths, security-sensitive code, generators, and agent
instructions. Keep privileged intake metadata-only. Run untrusted builds in a
separate pull_request workflow without secrets.

If maintainer mode is SOLO, import and follow
docs/solo-maintainer-administration.md, but leave its repository variable unset
until the acceptance and refusal checks below pass. Leave it unset for MULTI.

Run python3 tests/test_validate_pr.py and the repository's existing checks.
Show the diff, results, assumptions, and GitHub settings an administrator must
finish. Do not commit or push.
```

## Finish setup

1. Review the agent's diff and test output.
2. Complete the repository settings in the adopted `MAINTAINERS.md`.
3. Create the labels referenced by the adopted issue forms.
4. Open one valid and one deliberately invalid draft pull request.
5. Require `contribution-intake / validate-metadata` only after the valid and invalid draft pull requests behave as expected.
6. If SOLO was selected, enable the repository variable now.
