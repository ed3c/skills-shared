#!/usr/bin/env python3
"""Hermetic real-task A/B for the Agentic Tech Lead refactor.

The canary uses one immutable Git subject, real linked worktrees/subprocesses,
locked contracts/tests, path-disjoint fan-out, a three-candidate tournament,
checkpoint/resume, explicit convergence, and local/global oracles.  It measures
orchestration closure, not model quality: providers, Git Town, Forgejo, and
behavioral uplift remain NOT_EXERCISED.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "real-task-checkout-v1"
AUTHORITY = {"merge": False, "publication": False, "secret_access": False}
HISTORICAL = {
    "A_OLD_MONOLITH": ("tests/fixtures/pre-refactor-SKILL.txt", "a01f53592cda98f61b413b4467afa96356fb4ef7"),
    "B0_REFACTOR_AS_LANDED": ("tests/fixtures/refactor-as-landed-SKILL.txt", "8b2da7443aff7a9f53412b5af280048203bbd5e9"),
    "B1_REACHABILITY_REPAIRED": ("tests/fixtures/reachability-repaired-SKILL.txt", "51c3fd81749598957f2b993c4d31c3b4c8c277c1"),
}

CONTRACT = 'PRICING="apply_discount(int,int)->int"\nRECEIPT="render_receipt(int)->str"\nCHECKOUT="checkout(int,int)->str"\n'
ORACLES = {
    "pricing": 'import sys;sys.path.insert(0,"src");from pricing import apply_discount\nassert apply_discount(10000,2500)==7500\nassert apply_discount(199,3333)==132\nassert apply_discount(0,5000)==0\n',
    "receipt": 'import sys;sys.path.insert(0,"src");from receipt import render_receipt\nassert render_receipt(7500)=="$75.00"\nassert render_receipt(132)=="$1.32"\nassert render_receipt(0)=="$0.00"\n',
    "checkout_local": 'import sys;sys.path.insert(0,"src");from checkout import checkout\nassert checkout(10000,2500).endswith("$75.00")\n',
    "global": 'import sys;sys.path.insert(0,"src");from checkout import checkout\nassert checkout(10000,2500)=="TOTAL $75.00"\nassert checkout(199,3333)=="TOTAL $1.32"\nassert checkout(0,5000)=="TOTAL $0.00"\n',
}
CODE = {
    ("pricing", "minimal"): 'def apply_discount(subtotal_cents:int,rate_bps:int)->int:\n    return subtotal_cents*(10000-rate_bps)//10000\n',
    ("pricing", "defensive"): 'def apply_discount(subtotal_cents:int,rate_bps:int)->int:\n    if not isinstance(subtotal_cents,int) or not isinstance(rate_bps,int): raise TypeError\n    if subtotal_cents<0 or not 0<=rate_bps<=10000: raise ValueError\n    return subtotal_cents*(10000-rate_bps)//10000\n',
    ("pricing", "buggy"): 'def apply_discount(subtotal_cents:int,rate_bps:int)->int:\n    return round(subtotal_cents*(10000-rate_bps)/10000)\n',
    ("receipt", "standard"): 'def render_receipt(total_cents:int)->str:\n    return f"${total_cents//100}.{total_cents%100:02d}"\n',
    ("checkout", "convergence"): 'from pricing import apply_discount\nfrom receipt import render_receipt\ndef checkout(subtotal_cents:int,rate_bps:int)->str:\n    return f"TOTAL {render_receipt(apply_discount(subtotal_cents,rate_bps))}"\n',
    ("checkout", "local-only-buggy"): 'from pricing import apply_discount\nfrom receipt import render_receipt\ndef checkout(subtotal_cents:int,rate_bps:int)->str:\n    return render_receipt(apply_discount(subtotal_cents,rate_bps))\n',
}


class CanaryError(RuntimeError):
    pass


def proc(argv: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False, env=os.environ.copy())
    if check and result.returncode:
        raise CanaryError(f"command {result.returncode}: {' '.join(argv)}\n{result.stdout}\n{result.stderr}")
    return result


def git(repo: Path, *args: str, check: bool = True) -> str:
    return proc(["git", "-C", str(repo), *args], check=check).stdout.strip()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def blob(text: str) -> str:
    raw = text.encode(); return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def safe_path(value: str) -> Path:
    pure = PurePosixPath(value)
    if not value or pure.is_absolute() or ".." in pure.parts or pure.parts[:1] == (".git",):
        raise CanaryError(f"unsafe path {value}")
    return Path(*pure.parts)


def run_oracle(repo: Path, name: str) -> bool:
    return proc([sys.executable, f"oracles/{name}.py"], cwd=repo, check=False).returncode == 0


def build_subject(root: Path) -> tuple[Path, str, str]:
    repo = root / "subject"; repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "canary"); git(repo, "config", "user.email", "canary@example.invalid")
    for folder in ("src", "contracts", "oracles"): (repo / folder).mkdir()
    (repo / "src/.keep").write_text("")
    (repo / "contracts/checkout.py").write_text(CONTRACT)
    for name, source in ORACLES.items(): (repo / f"oracles/{name}.py").write_text(source)
    (repo / "README.md").write_text("Immutable contracts/oracles; Workers own only src/.\n")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", "fixture: frozen red task")
    return repo, git(repo, "rev-parse", "HEAD"), git(repo, "rev-parse", "HEAD^{tree}")


def worker(args: argparse.Namespace) -> int:
    time.sleep(args.delay_ms / 1000)
    target = args.worktree.resolve() / safe_path(args.owned_path)
    checkpoint = args.checkpoint.resolve(); checkpoint.parent.mkdir(parents=True, exist_ok=True)
    if args.task == "receipt" and not args.resume and not checkpoint.exists():
        dump(checkpoint, {"attempt": args.attempt, "state": "CHECKPOINTED", "head": git(args.worktree, "rev-parse", "HEAD")})
        return 75
    if args.resume and not checkpoint.exists(): raise CanaryError("resume without checkpoint")
    target.parent.mkdir(parents=True, exist_ok=True); target.write_text(CODE[(args.task, args.variant)])
    dump(checkpoint, {"attempt": args.attempt, "state": "RESULT_READY", "output": sha_file(target)})
    return 0


def add_worktree(repo: Path, root: Path, branch: str, base: str) -> Path:
    path = root / branch.replace("/", "__")
    git(repo, "worktree", "add", "-q", "-b", branch, str(path), base)
    return path


def remove_worktree(repo: Path, path: Path, branch: str) -> None:
    git(repo, "worktree", "remove", "--force", str(path), check=False)
    git(repo, "branch", "-D", branch, check=False)


def commit(repo: Path, message: str) -> str:
    git(repo, "config", "user.name", "worker"); git(repo, "config", "user.email", "worker@example.invalid")
    git(repo, "add", "-A"); git(repo, "commit", "-qm", message)
    return git(repo, "rev-parse", "HEAD")


def launch(script: Path, worktree: Path, task: str, variant: str, owned: str,
           checkpoint: Path, attempt: str, delay: int = 0, resume: bool = False) -> tuple[subprocess.Popen[str], int]:
    argv = [sys.executable, str(script), "worker", "--worktree", str(worktree), "--task", task,
            "--variant", variant, "--owned-path", owned, "--checkpoint", str(checkpoint),
            "--attempt", attempt, "--delay-ms", str(delay)]
    if resume: argv.append("--resume")
    return subprocess.Popen(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE), time.time_ns()


def graph_controls() -> dict[str, bool]:
    graph = {
        "pricing": {"deps": [], "consumes": {}},
        "receipt": {"deps": [], "consumes": {}},
        "checkout": {"deps": ["pricing", "receipt"], "consumes": {"pricing": ["src/pricing.py"], "receipt": ["src/receipt.py"]}},
    }
    def errors(value: dict[str, Any]) -> list[str]:
        out: list[str] = []
        for task, row in value.items():
            for dep in row["deps"]:
                if dep == task or dep not in value or not row["consumes"].get(dep): out.append(f"false-edge:{task}->{dep}")
            if set(row["consumes"]) - set(row["deps"]): out.append(f"orphan-consumption:{task}")
        def visit(node: str, active: set[str], done: set[str]) -> None:
            if node in active: out.append(f"cycle:{node}"); return
            if node in done: return
            active.add(node)
            for dep in value[node]["deps"]:
                if dep in value: visit(dep, active, done)
            active.remove(node); done.add(node)
        done: set[str] = set()
        for node in value: visit(node, set(), done)
        return out
    if errors(graph): raise CanaryError("valid graph rejected")
    fake = copy.deepcopy(graph); fake["receipt"]["deps"] = ["pricing"]
    leases = [
        {"path": "src/pricing.py", "task": "pricing", "replica": "pricing"},
        {"path": "src/pricing.py", "task": "pricing", "replica": "pricing"},
        {"path": "src/pricing.py", "task": "pricing", "replica": "pricing"},
        {"path": "src/receipt.py", "task": "receipt", "replica": ""},
    ]
    def lease_errors(value: list[dict[str, str]]) -> list[str]:
        out: list[str] = []
        for i, left in enumerate(value):
            for right in value[i + 1:]:
                allowed = left["path"] != right["path"] or (left["task"] == right["task"] and left["replica"] and left["replica"] == right["replica"])
                if not allowed: out.append(f"overlap:{left['path']}")
        return out
    if lease_errors(leases): raise CanaryError("valid tournament replicas rejected")
    bad_leases = leases + [{"path": "src/receipt.py", "task": "other", "replica": ""}]
    return {"fake_dependency_refused": bool(errors(fake)), "overlapping_writer_refused": bool(lease_errors(bad_leases)), "graph_digest": digest(graph)}
