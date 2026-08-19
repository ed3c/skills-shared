#!/usr/bin/env python3
import copy, importlib.util, json
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
        self.missing_label = False
        self.closed = False
        self.blocked_shape = "valid"

    def _blocked_connection(self):
        nodes = [
            {
                "number": x,
                "title": f"fixture {x}",
                "url": f"https://github.com/ed3c/skills-shared/issues/{x}",
                "state": "OPEN",
                "repository": {"nameWithOwner": "ed3c/skills-shared"},
            }
            for x in self.blocked
        ]
        conn = {"nodes": nodes, "totalCount": len(nodes)}
        if self.blocked_shape == "valid":
            return conn
        if self.blocked_shape == "legacy-list":
            return nodes
        if self.blocked_shape == "missing-total":
            return {"nodes": nodes}
        if self.blocked_shape == "extra-field":
            return {"nodes": nodes, "totalCount": len(nodes), "pageInfo": {}}
        if self.blocked_shape == "bad-total":
            return {"nodes": nodes, "totalCount": len(nodes) + 1}
        if self.blocked_shape == "bad-nodes":
            return {"nodes": {}, "totalCount": len(nodes)}
        if self.blocked_shape == "bad-number":
            bad = copy.deepcopy(nodes)
            bad[0]["number"] = str(bad[0]["number"])
            return {"nodes": bad, "totalCount": len(bad)}
        if self.blocked_shape == "cross-repo":
            bad = copy.deepcopy(nodes)
            bad[0]["repository"]["nameWithOwner"] = "other/repo"
            return {"nodes": bad, "totalCount": len(bad)}
        raise AssertionError(self.blocked_shape)

    def run(self, a):
        if a[:3] == ["gh", "repo", "view"]:
            return json.dumps(
                {
                    "nameWithOwner": "ed3c/skills-shared",
                    "visibility": "PUBLIC",
                    "defaultBranchRef": {"name": "main"},
                }
            )
        if a[:3] == ["gh", "issue", "view"]:
            n = int(a[3])
            fields = a[-1]
            if fields == "number,state,labels":
                return json.dumps(
                    {
                        "number": n,
                        "state": "CLOSED" if self.closed and n == 9002 else "OPEN",
                        "labels": []
                        if self.missing_label and n == 9001
                        else [{"name": "ctl-live-canary"}],
                    }
                )
            if fields == "blockedBy":
                return json.dumps({"blockedBy": self._blocked_connection()})
        if a[:3] == ["gh", "issue", "edit"]:
            if "--add-blocked-by" in a:
                n = int(a[a.index("--add-blocked-by") + 1])
                self.blocked = sorted(set(self.blocked + [n]))
                return ""
            if "--remove-blocked-by" in a:
                if self.cleanup_fail:
                    raise mod.ContractError("forced cleanup failure")
                n = int(a[a.index("--remove-blocked-by") + 1])
                self.blocked = [x for x in self.blocked if x != n]
                return ""
        raise AssertionError(a)


orig = mod._run
r = Remote()
mod._run = r.run
try:
    out = mod.execute(plan())
    assert out["canary_state"] == "LIVE_GITHUB_DEPENDENCY_CANARY_PASS"
    assert r.blocked == [8999]
finally:
    mod._run = orig


def fail(pm=lambda p: None, rm=lambda r: None):
    p = copy.deepcopy(plan())
    pm(p)
    r = Remote()
    rm(r)
    mod._run = r.run
    try:
        mod.execute(p)
    except mod.ContractError:
        return
    finally:
        mod._run = orig
    raise AssertionError("mutation passed")


fail(lambda p: p.update(blocker_issue=9002))
fail(lambda p: p.update(expected_before_blocked_by=[8999, 9001]))
fail(rm=lambda r: setattr(r, "blocked", [8998]))
fail(rm=lambda r: setattr(r, "missing_label", True))
fail(rm=lambda r: setattr(r, "closed", True))
fail(rm=lambda r: setattr(r, "cleanup_fail", True))

for shape in (
    "legacy-list",
    "missing-total",
    "extra-field",
    "bad-total",
    "bad-nodes",
    "bad-number",
    "cross-repo",
):
    fail(rm=lambda r, shape=shape: setattr(r, "blocked_shape", shape))


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
        "gh api \"repos/${REPO}/branches/main\"",
        "gh issue edit --help | grep -F -- '--add-blocked-by'",
        "gh issue edit --help | grep -F -- '--remove-blocked-by'",
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
    ]
    for fragment in forbidden:
        assert fragment not in workflow, fragment
    assert workflow.count("issues: write") == 1
    assert workflow.count("--add-blocked-by") >= 1
    assert workflow.count("--remove-blocked-by") >= 1

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
    "(positive=1 mutations=13 hosted-workflow=1 live=NOT_EXERCISED)"
)
