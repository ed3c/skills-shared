#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "github_issue_dag_projection.py"
spec = importlib.util.spec_from_file_location("dag", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

def graph():
    return {
        "repo": "ed3c/skills-shared",
        "repo_visibility": "PUBLIC",
        "default_branch": "main",
        "nodes": [
            {
                "issue": 1,
                "github_state": "CLOSED",
                "state": {"start_readable": True, "completion_admitted": True},
            },
            {
                "issue": 2,
                "github_state": "OPEN",
                "state": {"start_readable": True, "completion_admitted": False},
            },
            {
                "issue": 3,
                "github_state": "OPEN",
                "state": {"start_readable": False, "completion_admitted": False},
            },
        ],
        "edges": [
            {
                "blocker": 1,
                "blocked": 2,
                "readiness": "start",
                "project_to_github": False,
            },
            {
                "blocker": 2,
                "blocked": 3,
                "readiness": "completion",
                "project_to_github": True,
            },
        ],
    }

g = graph()
mod.validate_graph(g)
assert len(mod.canonical_graph_digest(g)) == 64
assert mod.desired_blocked_by(g) == {1: [], 2: [], 3: [2]}
assert mod.ready_wave(g) == [1, 2]
assert mod.compare_readback(
    g,
    {"1": {"blockedBy": []}, "2": {"blockedBy": []}, "3": {"blockedBy": [2]}},
)["match"]
extra = mod.compare_readback(
    g,
    {"1": {"blockedBy": []}, "2": {"blockedBy": []}, "3": {"blockedBy": [1, 2]}},
)
assert not extra["match"] and extra["extra"] == {"3": [1]}

def fail(mutator):
    candidate = copy.deepcopy(graph())
    mutator(candidate)
    try:
        mod.validate_graph(candidate)
    except mod.ContractError:
        return
    raise AssertionError("mutation passed")

fail(
    lambda x: x["edges"].append(
        {"blocker": 3, "blocked": 2, "readiness": "completion", "project_to_github": True}
    )
)
fail(
    lambda x: x["edges"].append(
        {"blocker": 1, "blocked": 1, "readiness": "completion", "project_to_github": True}
    )
)
fail(lambda x: x["edges"][0].update(project_to_github=True))
fail(lambda x: x["edges"].append(copy.deepcopy(x["edges"][0])))
fail(lambda x: x["edges"][0].update(blocker=99))
fail(lambda x: x.update(graph_digest="0" * 64))
fail(lambda x: x["nodes"][0].update(issue=True))
fail(lambda x: x.update(repo_visibility="UNKNOWN"))
fail(lambda x: x.update(default_branch=""))
fail(lambda x: x["nodes"][1].update(github_state="UNKNOWN"))

try:
    mod.compare_readback(g, {"1": {"blockedBy": []}, "2": {"blockedBy": []}})
except mod.ContractError:
    pass
else:
    raise AssertionError("incomplete readback passed")

def preflight_run(argv):
    if argv[:3] == ["gh", "repo", "view"]:
        return json.dumps(
            {
                "nameWithOwner": "ed3c/skills-shared",
                "visibility": "PUBLIC",
                "defaultBranchRef": {"name": "main"},
            }
        )
    if argv[:3] == ["gh", "issue", "view"]:
        issue = int(argv[3])
        return json.dumps(
            {
                "number": issue,
                "state": "CLOSED" if issue == 1 else "OPEN",
                "closedByPullRequestsReferences": [],
            }
        )
    raise AssertionError(argv)

orig_run = mod._run
orig_readback = mod.live_readback
orig_preflight = mod.live_preflight

try:
    mod._run = preflight_run
    observed = mod.live_preflight(g)
    assert observed["repository"]["nameWithOwner"] == "ed3c/skills-shared"
    assert observed["issues"]["1"]["state"] == "CLOSED"
finally:
    mod._run = orig_run

def preflight_must_fail(fake):
    mod._run = fake
    try:
        mod.live_preflight(g)
    except mod.ContractError:
        return
    finally:
        mod._run = orig_run
    raise AssertionError("preflight mutation passed")

def wrong_repo(argv):
    if argv[:3] == ["gh", "repo", "view"]:
        return json.dumps(
            {
                "nameWithOwner": "ed3c/other",
                "visibility": "PUBLIC",
                "defaultBranchRef": {"name": "main"},
            }
        )
    return preflight_run(argv)
preflight_must_fail(wrong_repo)

def wrong_visibility(argv):
    if argv[:3] == ["gh", "repo", "view"]:
        return json.dumps(
            {
                "nameWithOwner": "ed3c/skills-shared",
                "visibility": "PRIVATE",
                "defaultBranchRef": {"name": "main"},
            }
        )
    return preflight_run(argv)
preflight_must_fail(wrong_visibility)

def wrong_default_branch(argv):
    if argv[:3] == ["gh", "repo", "view"]:
        return json.dumps(
            {
                "nameWithOwner": "ed3c/skills-shared",
                "visibility": "PUBLIC",
                "defaultBranchRef": {"name": "trunk"},
            }
        )
    return preflight_run(argv)
preflight_must_fail(wrong_default_branch)

def stale_issue(argv):
    if argv[:3] == ["gh", "repo", "view"]:
        return preflight_run(argv)
    if argv[:3] == ["gh", "issue", "view"] and int(argv[3]) == 2:
        return json.dumps(
            {"number": 2, "state": "CLOSED", "closedByPullRequestsReferences": []}
        )
    return preflight_run(argv)
preflight_must_fail(stale_issue)

def duplicate_linked_pr(argv):
    if argv[:3] == ["gh", "repo", "view"]:
        return preflight_run(argv)
    if argv[:3] == ["gh", "issue", "view"] and int(argv[3]) == 2:
        return json.dumps(
            {
                "number": 2,
                "state": "OPEN",
                "closedByPullRequestsReferences": [
                    {"number": 101, "state": "OPEN"},
                    {"number": 102, "state": "OPEN"},
                ],
            }
        )
    return preflight_run(argv)
preflight_must_fail(duplicate_linked_pr)

calls = []
try:
    mod.live_preflight = lambda data: {
        "repository": {
            "nameWithOwner": data["repo"],
            "visibility": data["repo_visibility"],
            "default_branch": data["default_branch"],
        },
        "issues": {},
    }
    mod.live_readback = lambda repo, issues: {
        "1": {"blockedBy": []},
        "2": {"blockedBy": []},
        "3": {"blockedBy": [1, 2]},
    }
    mod._run = lambda argv: calls.append(argv) or ""
    try:
        mod.apply_projection(g)
    except mod.ContractError:
        pass
    else:
        raise AssertionError("destructive extra-edge reconciliation passed")
    assert calls == [], "extra blockers must fail before any mutation"
finally:
    mod.live_preflight = orig_preflight
    mod.live_readback = orig_readback
    mod._run = orig_run

# live_readback producer controls (#497): the real parser must consume the
# gh LinkedIssueConnection shape and fail closed on every other shape.
def connection_payload(blocked_by):
    return json.dumps({"blockedBy": blocked_by})

def node(number, repo="ed3c/skills-shared"):
    return {
        "number": number,
        "title": "t",
        "url": f"https://github.com/{repo}/issues/{number}",
        "state": "OPEN",
        "repository": {"nameWithOwner": repo},
    }

def readback_with(payload):
    def fake(argv):
        assert argv[:3] == ["gh", "issue", "view"], argv
        assert argv[-2:] == ["--json", "blockedBy"], argv
        return payload
    mod._run = fake
    try:
        return mod.live_readback("ed3c/skills-shared", [7])
    finally:
        mod._run = orig_run

observed = readback_with(
    connection_payload({"nodes": [node(6), node(5)], "totalCount": 2})
)
assert observed == {"7": {"blockedBy": [5, 6]}}, observed

def readback_must_fail(payload, why):
    try:
        readback_with(payload)
    except mod.ContractError:
        return
    raise AssertionError(why)

readback_must_fail(
    connection_payload([{"number": 5}]),
    "legacy bare-list blockedBy shape accepted",
)
readback_must_fail(
    connection_payload({"nodes": [node(5)], "totalCount": 2}),
    "totalCount mismatch accepted",
)
readback_must_fail(
    connection_payload({"nodes": [node(5, repo="other/repo")], "totalCount": 1}),
    "cross-repository blockedBy node accepted",
)
readback_must_fail(
    connection_payload({"nodes": [node(5), node(5)], "totalCount": 2}),
    "duplicate blockedBy numbers accepted",
)
readback_must_fail(
    connection_payload({"nodes": [{"number": "5"}], "totalCount": 1}),
    "non-int blockedBy number accepted",
)
readback_must_fail(
    connection_payload(
        {"nodes": [node(5)], "totalCount": 1, "pageInfo": {}}
    ),
    "extra connection keys accepted",
)

print("github-issue-dag selftest: PASS (positive=7 mutations=23 live=NOT_EXERCISED)")
