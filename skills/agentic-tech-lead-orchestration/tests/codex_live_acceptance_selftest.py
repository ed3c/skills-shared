#!/usr/bin/env python3
import copy, importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCRIPT=HERE.parent/"scripts"/"compile_codex_live_acceptance.py"
spec=importlib.util.spec_from_file_location("live",SCRIPT); mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
H40="a"*40; T40="b"*40; H64="c"*64

def packet():
    return {"worker_result":{"task_id":"T1","attempt_id":"A1","repo":"ed3c/skills-shared","base_sha":H40,"tree_sha":T40,"prompt_digest":H64,"adapter_state":"RUNTIME_RETURNED","sdk_execution":"EXERCISED","controller_readback_required":True,"lease_readback":"PASS","changed_files":["src/a.py"],"turn_status":"completed","thread_id":"thread-1","final_response_digest":"d"*64},"controller":{"task_id":"T1","attempt_id":"A1","repo":"ed3c/skills-shared","base_sha":H40,"tree_sha":T40,"changed_files":["src/a.py"],"source_diff_readback":"PASS","tests_readback":"PASS","commands":[{"command_sha256":"e"*64,"exit_code":0,"output_sha256":"f"*64}]}}
r=mod.compile_receipt(packet()); assert r["acceptance_state"]=="LIVE_RUNTIME_AND_CONTROLLER_READBACK_CANDIDATE" and r["shadow_review_required"] is True

def fail(fn):
    x=copy.deepcopy(packet()); fn(x)
    try: mod.compile_receipt(x)
    except mod.ContractError: return
    raise AssertionError("mutation passed")
fail(lambda x:x["worker_result"].update(sdk_execution="NOT_EXERCISED"))
fail(lambda x:x["worker_result"].update(lease_readback="FAIL"))
fail(lambda x:x["worker_result"].update(adapter_state="STATIC_VALIDATED"))
fail(lambda x:x["worker_result"].update(turn_status="failed"))
fail(lambda x:x["controller"].update(attempt_id="A2"))
fail(lambda x:x["controller"].update(changed_files=["src/b.py"]))
fail(lambda x:x["controller"].update(source_diff_readback="FAIL"))
fail(lambda x:x["controller"].update(tests_readback="FAIL"))
fail(lambda x:x["controller"].update(commands=[]))
fail(lambda x:x["controller"]["commands"][0].update(exit_code=1))
fail(lambda x:x["worker_result"].update(base_sha="abc"))
fail(lambda x:x["worker_result"].update(final_response="raw model prose"))
print("codex-live-acceptance selftest: PASS (positive=1 mutations=12 live=NOT_EXERCISED)")
