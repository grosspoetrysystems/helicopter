#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_pr import validate_body

SCRIPT = ROOT / "scripts" / "validate_pr.py"
TEMPLATE = ROOT / ".github" / "pull_request_template.md"


VALID_HUMAN = """## Change

Small fix.

## Human accountability

Accountable contributor: @alice

- [x] I reviewed the complete diff.
- [x] I understand and can explain the change.
- [x] I verified the evidence below.
- [x] I have the right to submit this contribution.

## Verification

Ran the check.

## Risk

- [x] None of the above

## AI / automation

- [x] Human-authored
- [ ] AI-assisted
- [ ] Agent-authored
- [ ] Authorized automation

Agent identity: `none`
Run ID: `none`
Base SHA: `none`

Capabilities:

```json
{
  "repository_write": false,
  "command_execution": false,
  "network": "none",
  "secrets": "none",
  "approve": false,
  "merge": false
}
```
"""


def codes(body: str) -> set[str]:
    return {refusal.code for refusal in validate_body(body)}


class ValidateBodyTests(unittest.TestCase):
    def test_valid_human_submission_passes(self) -> None:
        self.assertEqual(codes(VALID_HUMAN), set())

    def test_accountability_must_be_real_and_confirmed(self) -> None:
        body = VALID_HUMAN.replace("@alice", "@YOUR_GITHUB_USERNAME").replace(
            "[x] I reviewed the complete diff.", "[ ] I reviewed the complete diff."
        )
        self.assertEqual(
            codes(body),
            {"REFUSE_HUMAN_ACCOUNTABILITY_MISSING", "REFUSE_ACCOUNTABILITY_UNCONFIRMED"},
        )

    def test_exactly_one_origin_is_required(self) -> None:
        body = VALID_HUMAN.replace("[ ] AI-assisted", "[x] AI-assisted")
        self.assertIn("REFUSE_AGENT_ORIGIN_AMBIGUOUS", codes(body))

    def test_agent_submission_requires_identity_and_provenance(self) -> None:
        body = VALID_HUMAN.replace("[x] Human-authored", "[ ] Human-authored").replace(
            "[ ] Agent-authored", "[x] Agent-authored"
        )
        self.assertEqual(
            codes(body),
            {"REFUSE_AGENT_IDENTITY_UNKNOWN", "REFUSE_PROVENANCE_INCOMPLETE"},
        )

    def test_valid_agent_submission_passes(self) -> None:
        body = (
            VALID_HUMAN.replace("[x] Human-authored", "[ ] Human-authored")
            .replace("[ ] Agent-authored", "[x] Agent-authored")
            .replace("Agent identity: `none`", "Agent identity: `builder[bot]`")
            .replace("Run ID: `none`", "Run ID: `run-123`")
            .replace("Base SHA: `none`", "Base SHA: `" + "a" * 40 + "`")
        )
        self.assertEqual(codes(body), set())

    def test_agent_cannot_claim_secrets_or_merge(self) -> None:
        body = (
            VALID_HUMAN.replace("[x] Human-authored", "[ ] Human-authored")
            .replace("[ ] Agent-authored", "[x] Agent-authored")
            .replace("Agent identity: `none`", "Agent identity: `builder[bot]`")
            .replace("Run ID: `none`", "Run ID: `run-123`")
            .replace("Base SHA: `none`", "Base SHA: `" + "a" * 40 + "`")
            .replace('"secrets": "none"', '"secrets": "repository"')
            .replace('"merge": false', '"merge": true')
        )
        self.assertEqual(codes(body), {"REFUSE_SECRET_ACCESS", "REFUSE_AGENT_SELF_APPROVAL"})

    def test_agent_capabilities_must_match_template(self) -> None:
        body = (
            VALID_HUMAN.replace("[x] Human-authored", "[ ] Human-authored")
            .replace("[ ] Agent-authored", "[x] Agent-authored")
            .replace("Agent identity: `none`", "Agent identity: `builder[bot]`")
            .replace("Run ID: `none`", "Run ID: `run-123`")
            .replace("Base SHA: `none`", "Base SHA: `" + "a" * 40 + "`")
            .replace('"network": "none"', '"network": true')
        )
        self.assertIn("REFUSE_CAPABILITIES_INVALID", codes(body))

    def test_shipped_template_matches_validator_contract(self) -> None:
        body = (
            TEMPLATE.read_text(encoding="utf-8")
            .replace("@YOUR_GITHUB_USERNAME", "@alice")
            .replace("- [ ] I ", "- [x] I ")
            .replace("- [ ] Human-authored", "- [x] Human-authored")
        )
        self.assertEqual(codes(body), set())

    def test_cli_accepts_a_valid_event(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event = Path(directory) / "event.json"
            event.write_text(json.dumps({"pull_request": {"body": VALID_HUMAN}}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(event)],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Human review is still required", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
