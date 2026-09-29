# Start a new repository

## Requirements

- [Git](https://git-scm.com/downloads)
- Python 3.10 or newer
- [GitHub CLI](https://github.com/cli/cli#installation)
- Permission to create and administer the repository

Authenticate before starting:

```sh
gh auth login --web
gh auth status
```

## Create the repository

Choose the owner, name, and visibility:

```sh
gh repo create OWNER/PROJECT \
  --template grosspoetrysystems/helicopter \
  --private \
  --clone
cd PROJECT
```

Use `--public` instead of `--private` for a public repository.

## Agent prompt

Open the new directory in your coding agent and paste:

```text
Adapt this repository for the following project:

- Name: <PROJECT_NAME>
- Purpose: <ONE_SENTENCE_PURPOSE>
- Language/runtime: <STACK>
- GitHub owner: <OWNER>
- Maintainer or team: <CODEOWNER>
- Private security contact: <CONTACT_OR_GITHUB_PRIVATE_REPORTING>
- Contribution agreement: <DCO_OR_CLA>
- Maintainer mode: <SOLO_OR_MULTI>

Replace Helicopter-specific names, URLs, owners, contacts, labels, and
contribution terms. Keep the metadata intake workflow limited to protected
default-branch metadata; never check out or execute pull-request code in `pull_request_target`.
Add project build and test CI in a separate pull_request workflow. Extend
CODEOWNERS for dependencies, lockfiles, release paths, security-sensitive code,
generators, and agent instructions that exist in this project.

If maintainer mode is SOLO, follow docs/solo-maintainer-administration.md, but
leave its repository variable unset until the acceptance and refusal checks
below pass. Leave it unset for MULTI.

Run python3 tests/test_validate_pr.py and the project's checks. Report changed
files, results, and GitHub settings that still need an administrator.
```

## Finish setup

1. Review the agent's diff and test output.
2. Complete the repository settings in [`MAINTAINERS.md`](../MAINTAINERS.md).
3. Create the `needs-triage` and `automation-review` labels, or update the issue forms to use existing labels.
4. Open one valid and one deliberately invalid draft pull request.
5. Require `contribution-intake / validate-metadata` only after the valid and invalid draft pull requests behave as expected.
6. If SOLO was selected, enable the repository variable now.
