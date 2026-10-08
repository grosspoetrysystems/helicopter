# Solo-maintainer administration

Helicopter's contributor controls protect a maintainer from untrusted submissions. They should not turn the sole maintainer into an external contributor to their own repository.

Solo-maintainer mode is disabled by default. It exempts one configured human maintainer of a personal or organization-owned repository from Helicopter's pull-request metadata contract. It does not bypass project CI, release controls, or GitHub rulesets.

## Enable solo-maintainer mode

After the repository exists, set both Actions repository variables:

```sh
REPOSITORY=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
MAINTAINER_ID=$(gh api user --jq .id)
gh variable set HELICOPTER_SOLO_MAINTAINER_ID --body "$MAINTAINER_ID" --repo "$REPOSITORY"
gh variable set HELICOPTER_SOLO_MAINTAINER_MODE --body true --repo "$REPOSITORY"
```

Set these variables on the repository, never at organization scope. GitHub includes organization variables in the same `vars` context; organization-scoped solo-mode variables could affect every repository that inherits them.

The intake workflow accepts the exemption only when all of these event fields and settings agree:

1. `HELICOPTER_SOLO_MAINTAINER_ID` is a positive decimal GitHub user ID;
2. the pull-request author and event sender are both type `User` with that immutable ID;
3. for a personal repository, that ID is also the repository owner's ID;
4. for an organization-owned repository, the configured user is the explicitly authorized sole maintainer;
5. the event repository and pull-request base and head repositories have the same repository ID, so the pull request is not from a fork.

The variables are repository configuration, not template content, so repositories created from Helicopter do not inherit them. Pull requests cannot set them. A repository administrator can change them, but that administrator already controls repository settings and workflows.

Delete both variables before requiring another maintainer to follow the normal contributor path:

```sh
gh variable delete HELICOPTER_SOLO_MAINTAINER_MODE --repo "$REPOSITORY"
gh variable delete HELICOPTER_SOLO_MAINTAINER_ID --repo "$REPOSITORY"
```

## What the mode changes

- **Required CI** still proves a commit passed repository checks.
- **Contributor admission** still requires provenance, attestations, and maintainer review from other contributors, bots, and forks.
- **Maintainer authority** may skip only Helicopter's metadata form when the configured sole maintainer opens a pull request from the governed repository.

The exemption returns success before parsing the pull-request body. It does not auto-check human attestations or invent provenance. Keep contributor, fork, and bot paths unchanged.

## Pull requests are optional for the maintainer

A pull request remains useful for a web diff, pre-merge CI, discussion, and a merge boundary. It is not the sole maintainer's security boundary.

A direct administrator push is appropriate when the maintainer has reviewed a small change locally and accepts that required checks run after the commit reaches the default branch. With classic branch protection and administrator enforcement disabled, GitHub reports that the push bypassed expected checks; this is configured maintainer authority, not proof that checks ran before landing.

Do not attach production publication to every default-branch push merely because direct pushes are allowed. Separate:

```text
push or merge to main  -> CI only
explicit site deploy   -> production site/landing publication
version tag or release -> CLI/package publication
```

A direct push is otherwise capable of deploying before its same-event CI jobs finish. Release and deploy workflows should retain their own credentials and least-privilege permissions.

## GitHub settings

A practical initial configuration is:

- protect the default branch;
- require the repository's build, test, and intake status checks;
- require branches to be up to date when that cost is acceptable;
- do not require approving reviews while there is only one maintainer;
- do not enforce branch protection for administrators;
- keep production deploy and release triggers explicit;
- document that contributor approval is maintainer practice until GitHub can enforce it without deadlocking the owner.

Inspect classic branch protection:

```sh
gh api repos/OWNER/REPO/branches/main/protection
```

Enumerate classic branch-protection patterns, including wildcard rules:

```sh
gh api graphql -f query='{
  repository(owner:"OWNER", name:"REPO") {
    branchProtectionRules(first:100) {
      nodes {
        pattern
        isAdminEnforced
        requiresApprovingReviews
        requiredApprovingReviewCount
        requiresCodeOwnerReviews
        requireLastPushApproval
        requiresStatusChecks
      }
    }
  }
}'
```

Inspect repository rulesets and effective ruleset rules for a branch:

```sh
gh api repos/OWNER/REPO/rulesets
gh api repos/OWNER/REPO/rules/branches/main
```

The per-branch rules endpoint reports rulesets, not classic branch protection. An empty array does not prove that a branch is unprotected; query both surfaces. Organization rulesets may also require an `admin:org` token scope to enumerate.

After changing required status checks, verify the whole object. Updating the contexts can accidentally loosen strictness if the request omits it:

```sh
gh api repos/OWNER/REPO/branches/main/protection/required_status_checks \
  -q '{strict: .strict, contexts: .contexts}'
```

## Trusted intake and bootstrap changes

A metadata intake workflow commonly uses `pull_request_target`. It must load its validator from `github.event.repository.default_branch`, not the pull request's target branch. This keeps the validator on a maintainer-controlled commit even for stacked pull requests that target another branch.

The workflow and validator wiring that reads `HELICOPTER_SOLO_MAINTAINER_MODE` and `HELICOPTER_SOLO_MAINTAINER_ID` must already exist on the protected default branch. Repository variables are read at run time, so `gh variable set` takes effect on the next pull-request event.

Until that wiring reaches the default branch, the maintainer's pull request follows the normal metadata contract. Complete the template rather than inventing an agent run ID or auto-checking attestations.

## Stacked pull requests

GitHub can identify dependent pull requests as a stack. The normal GraphQL merge mutation may reject one with a message requiring the asynchronous REST merge endpoint:

```text
PUT /repos/OWNER/REPO/pulls/NUMBER/merge-async
```

A `202` response only enqueues the merge. Poll the returned UUID until the result is `merged` or `failed`:

```text
GET /repos/OWNER/REPO/pulls/NUMBER/merge-async/UUID
```

The async endpoint evaluates protection in the background and has no administrator-override parameter. A failing required check can therefore reject an enqueued merge even when administrators normally bypass protection. Prefer landing the bottom bootstrap change first, then rebase or retarget the remaining stack so each later pull request passes normally.

Use merge commits for a stacked bootstrap when preserving the bottom branch's commits in the default branch avoids unnecessary rebases. A squash merge creates a new default-branch commit that is absent from the next branch; strict up-to-date checks will then require restacking.

## When a second maintainer joins

Re-enable required approving reviews and CODEOWNERS enforcement when another eligible human can review the maintainer's pull requests. At that point:

1. delete the `HELICOPTER_SOLO_MAINTAINER_MODE` and `HELICOPTER_SOLO_MAINTAINER_ID` repository variables;
2. require at least one approval;
3. require CODEOWNERS review for protected paths;
4. decide whether the last pusher must receive another person's approval;
5. retain administrator bypass for emergencies, or explicitly enforce protection for administrators;
6. update written policy in the same change as the GitHub setting.

Do not enable a control that no current person can satisfy. A permanently bypassed rule adds friction and trains maintainers to ignore protection warnings without adding review.

## References

- [Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews)
- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [About CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [REST API endpoints for repository rules](https://docs.github.com/en/rest/repos/rules)
- [REST API endpoints for pull requests](https://docs.github.com/en/rest/pulls/pulls)
- [REST API endpoints for users](https://docs.github.com/en/rest/users/users)
