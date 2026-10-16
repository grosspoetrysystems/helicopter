import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import dev_checks  # noqa: E402

SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
DIGEST = "31b9aac6ab067bada9a0c1b001d30ebc500ea4487e00a93c18c59b9ef5fa66db"


def workflow(trigger: str, steps: str) -> str:
    return f"on:\n  {trigger}:\njobs:\n  job:\n    runs-on: ubuntu-latest\n    steps:\n{steps}"


TRUSTED_CHECKOUT = (
    f"      - uses: actions/checkout@{SHA}\n"
    "        with:\n"
    "          ref: ${{ github.event.repository.default_branch }}\n"
)


class WorkflowInvariants(unittest.TestCase):
    def test_pinned_actions_and_trusted_checkout_pass(self):
        steps = TRUSTED_CHECKOUT + f"      - uses: docker://pragent/pr-agent@sha256:{DIGEST}\n"
        self.assertEqual(dev_checks.workflow_problems("w.yml", workflow("pull_request_target", steps)), [])

    def test_tag_pinned_action_fails(self):
        problems = dev_checks.workflow_problems("w.yml", workflow("pull_request", "      - uses: actions/checkout@v4\n"))
        self.assertEqual(len(problems), 1)
        self.assertIn("not pinned", problems[0])

    def test_unpinned_image_fails(self):
        steps = "      - uses: docker://pragent/pr-agent:latest\n"
        self.assertTrue(dev_checks.workflow_problems("w.yml", workflow("pull_request", steps)))

    def test_privileged_checkout_without_trusted_ref_fails(self):
        steps = f"      - uses: actions/checkout@{SHA}\n      - run: echo hi\n"
        problems = dev_checks.workflow_problems("w.yml", workflow("pull_request_target", steps))
        self.assertTrue(any("privileged checkout" in p for p in problems))

    def test_privileged_reference_to_pr_head_fails(self):
        steps = TRUSTED_CHECKOUT + "      - run: git fetch origin ${{ github.event.pull_request.head.sha }}\n"
        problems = dev_checks.workflow_problems("w.yml", workflow("issue_comment", steps))
        self.assertTrue(any("pull request head" in p for p in problems))

    def test_unprivileged_workflow_may_check_out_pr_code(self):
        steps = f"      - uses: actions/checkout@{SHA}\n"
        self.assertEqual(dev_checks.workflow_problems("w.yml", workflow("pull_request", steps)), [])

    def test_repository_workflows_pass(self):
        root = Path(__file__).resolve().parents[1] / ".github/workflows"
        problems = [p for f in root.glob("*.y*ml") for p in dev_checks.workflow_problems(f.name, f.read_text())]
        self.assertEqual(problems, [])


class ChangelogGate(unittest.TestCase):
    def test_shipped_change_without_fragment_fails(self):
        self.assertTrue(dev_checks.missing_fragment(["scripts/pr_queue.py"]))

    def test_shipped_change_with_fragment_passes(self):
        self.assertFalse(dev_checks.missing_fragment(["scripts/pr_queue.py", ".changes/unreleased/Fixed-20261016-180000.yaml"]))

    def test_development_only_change_needs_no_fragment(self):
        self.assertFalse(dev_checks.missing_fragment(["tests/test_ramp.py", "AGENTS.md", "lefthook.yml"]))


class CommitSubject(unittest.TestCase):
    def test_conventional_subjects_pass(self):
        for subject in ("feat: add the ramp", "fix(queue): count hours", "refactor!: drop the shim"):
            self.assertTrue(dev_checks.SUBJECT.match(subject), subject)

    def test_other_subjects_fail(self):
        for subject in ("Add the ramp", "feat:missing space", "feature: add", "fix(Queue): caps"):
            self.assertFalse(dev_checks.SUBJECT.match(subject), subject)


if __name__ == "__main__":
    unittest.main()
