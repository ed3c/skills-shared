#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO_ROOT = HERE.parents[2]
SCRIPT = ROOT / "scripts" / "github_issue_dag_live_canary.py"
spec = importlib.util.spec_from_file_location("canary", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def plan():
    return {
        "repo": "ed3c/skills-shared",
        "repo_visibility": "PUBLIC",
        "default_branch": "main",
        "blocker_issue": 9001,
        "blocked_issue": 9002,
        "canary_label": "ctl-live-canary",
        "expected_before_blocked_by": [8999],
    }


class Remote:
    def __init__(self):
        self.blocked = [8999]
        self.cleanup_fail = False
        self.add_fail = False
        self.missing_label = False
        self.closed = False
        self.malformed_blocked = False
        self.cross_repo = False
        self.bad_rest_id = False
        self.rest_ids = {8999: 18999, 9001: 19001, 9002: 19002}

    def run(self, argv):
        if argv[:3] == ["gh", "repo", "view"]:
            return json.dumps(
                {
                    "nameWithOwner": "ed3c/skills-shared",
                    "visibility": "PUBLIC",
                    "defaultBranchRef": {"name": "main"},
                }
            )
        if argv[:3] == ["gh", "issue", "view"]:
            number = int(argv[3])
            fields = argv[-1]
            if fields == "number,state,labels":
                return json.dumps(
                    {
                        "number": number,
                        "state": "CLOSED" if self.closed and number == 9002 else "OPEN",
                        "labels": []
                        if self.missing_label and number == 9001
                        else [{"name": "ctl-live-canary"}],
                    }
                )
        if argv[:2] == ["gh", "api"]:
            endpoint = argv[2]
            prefix = "repos/ed3c/skills-shared/issues/"
            if endpoint.startswith(prefix) and "/dependencies/" not in endpoint:
                number = int(endpoint.removeprefix(prefix))
                if "--jq" in argv and argv[argv.index("--jq") + 1] == ".id":
                    if self.bad_rest_id and number == 9001:
                        return "not-an-int\n"
                    return f"{self.rest_ids[number]}\n"
            if endpoint == (
                "repos/ed3c/skills-shared/issues/9002/"
                "dependencies/blocked_by?per_page=100"
            ):
                rows = []
                for number in self.blocked:
                    rows.append(
                        {
                            "number": str(number)
                            if self.malformed_blocked
                            else number,
                            "repository_url": (
                                "https://api.github.com/repos/other/repo"
                                if self.cross_repo
                                else "https://api.github.com/repos/ed3c/skills-shared"
                            ),
                        }
                    )
                return json.dumps([rows])
            if endpoint == (
                "repos/ed3c/skills-shared/issues/9002/dependencies/blocked_by"
            ) and argv[argv.index("--method") + 1] == "POST":
                if self.add_fail:
                    raise mod.ContractError("forced add failure")
                issue_id = int(argv[argv.index("-F") + 1].split("=", 1)[1])
                number = next(
                    n for n, rest_id in self.rest_ids.items() if rest_id == issue_id
                )
                self.blocked = sorted(set(self.blocked + [number]))
                return ""
            remove_prefix = (
                "repos/ed3c/skills-shared/issues/9002/dependencies/blocked_by/"
            )
            if endpoint.startswith(remove_prefix) and argv[argv.index("--method") + 1] == "DELETE":
                if self.cleanup_fail:
                    raise mod.ContractError("forced cleanup failure")
                issue_id = int(endpoint.removeprefix(remove_prefix))
                number = next(
                    n for n, rest_id in self.rest_ids.items() if rest_id == issue_id
                )
                self.blocked = [x for x in self.blocked if x != number]
                return ""
        raise AssertionError(argv)


orig = mod._run
remote = Remote()
mod._run = remote.run
try:
    out = mod.execute(plan())
    assert out["canary_state"] == "LIVE_GITHUB_DEPENDENCY_CANARY_PASS"
    assert remote.blocked == [8999]
finally:
    mod._run = orig


def fail(plan_mutation=lambda p: None, remote_mutation=lambda r: None):
    candidate = copy.deepcopy(plan())
    plan_mutation(candidate)
    remote = Remote()
    remote_mutation(remote)
    mod._run = remote.run
    try:
        mod.execute(candidate)
    except mod.ContractError:
        return
    finally:
        mod._run = orig
    raise AssertionError("mutation passed")


fail(lambda p: p.update(blocker_issue=9002))
fail(lambda p: p.update(expected_before_blocked_by=[8999, 9001]))
fail(remote_mutation=lambda r: setattr(r, "blocked", [8998]))
fail(remote_mutation=lambda r: setattr(r, "missing_label", True))
fail(remote_mutation=lambda r: setattr(r, "closed", True))
fail(remote_mutation=lambda r: setattr(r, "cleanup_fail", True))
fail(remote_mutation=lambda r: setattr(r, "add_fail", True))
fail(remote_mutation=lambda r: setattr(r, "malformed_blocked", True))
fail(remote_mutation=lambda r: setattr(r, "cross_repo", True))
fail(remote_mutation=lambda r: setattr(r, "bad_rest_id", True))


def assert_hosted_workflow_contract():
    plan_path = REPO_ROOT / ".github/canaries/wave3-github-dependency-live-plan.json"
    workflow_path = REPO_ROOT / ".github/workflows/wave3-github-dependency-live-canary.yml"
    governance_path = REPO_ROOT / ".github/workflows/wave3-github-dependency-live-canary-governance.yml"

    fixture_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert fixture_plan == {
        "repo": "ed3c/skills-shared",
        "repo_visibility": "PUBLIC",
        "default_branch": "main",
        "blocker_issue": 486,
        "blocked_issue": 487,
        "canary_label": "wave3-live-canary-fixture",
        "expected_before_blocked_by": [],
    }, fixture_plan
    mod.validate_plan(fixture_plan)

    workflow = workflow_path.read_text(encoding="utf-8")
    required = [
        "types: [ready_for_review]",
        "contents: read",
        "issues: write",
        "github.event.pull_request.head.repo.full_name == github.repository",
        "github.event.pull_request.base.ref == 'main'",
        "github.event.pull_request.head.ref == 'canary/465-github-dependency-live-run'",
        "github.event.pull_request.title == '[LIVE-CANARY][#465] Execute GitHub dependency canary'",
        "ref: ${{ github.event.pull_request.base.sha }}",
        "persist-credentials: false",
        "RECEIPT: /tmp/wave3-github-dependency-live-receipt.json",
        "GITHUB_API_VERSION: '2026-03-10'",
        'X-GitHub-Api-Version: ${GITHUB_API_VERSION}',
        "gh api \"repos/${REPO}/branches/main\"",
        "dependencies/blocked_by?per_page=100",
        "BLOCKER_ISSUE: '486'",
        "BLOCKED_ISSUE: '487'",
        "EVIDENCE_ISSUE: '465'",
        "github_issue_dag_live_canary_selftest.py",
        "github_issue_dag_live_canary.py",
        "--execute",
        "Path(os.environ['RECEIPT'])",
        "Draft202012Validator(schema).validate(receipt)",
        "assert receipt['before']['blockedBy'] == []",
        "assert receipt['applied']['blockedBy'] == [486]",
        "assert receipt['cleanup']['blockedBy'] == []",
        "LIVE_GITHUB_DEPENDENCY_CANARY_PASS",
        "REMOTE_CANARY_EDGE_ONLY",
        "gh issue comment \"${EVIDENCE_ISSUE}\"",
    ]
    for fragment in required:
        assert fragment in workflow, fragment
    forbidden = [
        "pull_request_target",
        "workflow_dispatch",
        "repository_dispatch",
        "contents: write",
        "actions: write",
        "secrets.",
        "github.event.pull_request.head.sha",
        "${{ runner.temp }}",
        "gh issue edit --help",
    ]
    for fragment in forbidden:
        assert fragment not in workflow, fragment
    assert workflow.count("issues: write") == 1

    carrier = SCRIPT.read_text(encoding="utf-8")
    for fragment in [
        'API_VERSION = "2026-03-10"',
        "/dependencies/blocked_by?per_page=100",
        '"--paginate"',
        '"--slurp"',
        '"POST"',
        '"DELETE"',
        'f"issue_id={blocker_rest_id}"',
        "cross-repository blockedBy forbidden for canary fixture",
        "canary cleanup failed after remote mutation",
    ]:
        assert fragment in carrier, fragment
    for fragment in ["--add-blocked-by", "--remove-blocked-by"]:
        assert fragment not in carrier, fragment

    governance = governance_path.read_text(encoding="utf-8")
    for fragment in [
        "contents: read",
        ".github/canaries/wave3-github-dependency-live-plan.json",
        ".github/workflows/wave3-github-dependency-live-canary.yml",
        ".github/workflows/wave3-github-dependency-live-canary-governance.yml",
        "skills/agentic-tech-lead-orchestration/scripts/github_issue_dag_live_canary.py",
        "skills/agentic-tech-lead-orchestration/tests/github_issue_dag_live_canary_selftest.py",
        "python3 skills/agentic-tech-lead-orchestration/tests/github_issue_dag_live_canary_selftest.py",
        "python3 scripts/check_commit_roles.py --repo-root .",
    ]:
        assert fragment in governance, fragment
    for fragment in ["issues: write", "contents: write", "pull_request_target", "secrets."]:
        assert fragment not in governance, fragment


assert_hosted_workflow_contract()
print(
    "github-dag-live-canary selftest: PASS "
    "(positive=1 mutations=10 hosted-workflow=1 live=NOT_EXERCISED)"
)
