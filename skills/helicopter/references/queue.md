# The review queue

Every open pull request from an outside contributor carries one label saying whose turn it is. In `team` mode, members' pull requests are queued too. The queue recomputes the label from the pull request's timeline every hour and on every pull request event, so labels are outputs: setting one by hand is overwritten. The one exception is removing `queue:possibly-superseded`, which dismisses it.

| Label | Whose turn | What happens next |
| --- | --- | --- |
| `queue:awaiting-reviewer` | A maintainer's | The clock runs. After 7 days (`HELICOPTER_QUEUE_NUDGE_HOURS`), one comment reminds the requested reviewers. |
| `queue:awaiting-author` | The contributor's | Set after a refused admission check or a maintainer's **Request changes**. Push your fix or reply, or press **Re-request review**, and it's the maintainer's turn again. |
| `queue:no-capacity` | Nobody's yet | A maintainer's turn lasted 21 days (`HELICOPTER_QUEUE_PAUSE_HOURS`). The pull request stays open and keeps its place; the comment says so publicly instead of leaving it silent. |
| `queue:possibly-superseded` | Unchanged | Another pull request for the same issue merged while this one waited. One comment names it. A maintainer closes it, or removes the label to dismiss the notice for good. |

Not queued: drafts, the maintainer's own pull requests outside `team` mode, and pull requests from bots on branches of this repository (treated as the maintainer's own work).

Once an hour, if `.github/helicopter/version.json` names an older release than Helicopter's latest, the queue opens one issue, "Helicopter VERSION is available". Close it to skip that release; it isn't reopened. Repositories with Dependabot also get a pull request bumping `.github/workflows/helicopter-release.yml`, which can carry the update itself.

The queue never closes or merges anything, and never changes a review requirement.
