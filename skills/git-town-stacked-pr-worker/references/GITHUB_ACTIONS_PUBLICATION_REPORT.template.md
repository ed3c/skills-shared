# GitHub Actions publication completion fragment

Append this fragment to the base `COMPLETION_REPORT.template.md` whenever the Worker could publish to GitHub.
Do not collapse any row into another.

## Publication subject

```text
publication intent: <initial-pr|ready-for-review|batched-repair|NONE>
local HEAD: <40_HEX_SHA>
local verification receipt: <REF_AND_SHA256>
GitHub snapshot: <REF_AND_SHA256>
publication-gate version/subject: <REF>
PR number: <NUMBER_OR_ABSENT>
remote head before: <SHA_OR_ABSENT>
remote head after: <SHA_OR_NOT_PUBLISHED>
stable trusted check: <NAME>
```

## Publication evidence lanes

| Lane | State | Exit/result | Subject | Receipt/evidence |
|---|---|---|---|---|
| local Git Town sync | `<STATE>` | `<RESULT>` | `<LOCAL_HEAD>` | `<REF>` |
| exact-HEAD local verification | `<STATE>` | `<EXIT>` | `<LOCAL_HEAD>` | `<REF>` |
| publication decision | `ALLOW|BLOCK|INVALID_POLICY_INPUT|NOT_EXERCISED` | `<REASON>` | `<LOCAL_HEAD>` | `<REF>` |
| remote publication | `PASS|FAIL|NOT_EXERCISED|SKIPPED_BY_POLICY` | `<OPERATION_OR_NONE>` | `<REMOTE_HEAD_OR_NONE>` | `<REF>` |
| post-push remote ancestry | `<STATE>` | `<RESULT>` | `<REMOTE_HEAD_OR_NONE>` | `<REF>` |
| GitHub trusted check | `<STATE>` | `<CONCLUSION_OR_NO_RUNNER>` | `<EXACT_REMOTE_HEAD>` | `<RUN_OR_CHECK_REF>` |
| billing circuit | `closed|billing-open|unknown` | `<BLOCKER_OR_NONE>` | `<OBSERVED_AT>` | `<SNAPSHOT_REF>` |
| owner recovery receipt | `<STATE>` | `<RECOVERY_RESULT>` | `<BLOCKER_TIMESTAMP>` | `<REF_OR_NONE>` |
| Human Admit | `<STATE>` | `<DECISION_OR_NONE>` | `<PR_HEAD>` | `<REF_OR_NONE>` |

## Cadence and cost controls

```text
draft PR runner-backed job requested: <NO_OR_POLICY_FAILURE>
obsolete head cancelled: <YES|NO|NOT_APPLICABLE|NOT_EXERCISED>
feature-branch push trigger present: <MUST_BE_NO_OR_REVIEWED_EXCEPTION>
feedback identity: <ID_OR_NONE>
feedback consumed by SHA: <SHA_OR_NONE>
artifact upload policy: <FAILURE_ONLY|RELEASE_ONLY|REVIEWED_EXCEPTION>
heavy physical workflow triggered: <NO|MANUAL_WITH_REF|NOT_EXERCISED>
```

## Required blocked-state reporting

When `billing-open`, report exactly:

```text
GitHub Actions account/runner allocation: BLOCKED_INFRASTRUCTURE
repository tests: NOT_EXERCISED
push/rerun/no-op commit: BLOCKED_BY_POLICY
owner recovery required: YES
```

Do not report the unstarted job as test FAIL or PASS. A recovery receipt permits one attempt; it is not a
runner-success receipt.

## Remaining authority

```text
merge: HUMAN_OWNED
permission or branch-protection change: HUMAN_OWNED
billing recovery assertion: OWNER_OWNED
release promotion: HUMAN_OWNED
production deployment: HUMAN_OWNED
```
