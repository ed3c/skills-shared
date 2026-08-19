#!/usr/bin/env python3
import copy, importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCRIPT=HERE.parent/"scripts"/"github_issue_dag_projection.py"
spec=importlib.util.spec_from_file_location("dag",SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def graph():
    return {
      "repo":"ed3c/skills-shared",
      "nodes":[
        {"issue":1,"state":{"start_readable":True,"completion_admitted":True}},
        {"issue":2,"state":{"start_readable":True,"completion_admitted":False}},
        {"issue":3,"state":{"start_readable":False,"completion_admitted":False}},
      ],
      "edges":[
        {"blocker":1,"blocked":2,"readiness":"start","project_to_github":False},
        {"blocker":2,"blocked":3,"readiness":"completion","project_to_github":True},
      ],
    }

g=graph(); mod.validate_graph(g)
assert mod.desired_blocked_by(g)=={1:[],2:[],3:[2]}
assert mod.ready_wave(g)==[1,2]
assert mod.compare_readback(g,{"1":{"blockedBy":[]},"2":{"blockedBy":[]},"3":{"blockedBy":[2]}})["match"]
assert not mod.compare_readback(g,{"1":{"blockedBy":[]},"2":{"blockedBy":[]},"3":{"blockedBy":[1]}})["match"]

def fail(mut):
    x=copy.deepcopy(graph()); mut(x)
    try: mod.validate_graph(x)
    except mod.ContractError:return
    raise AssertionError("mutation passed")

fail(lambda x:x["edges"].append({"blocker":3,"blocked":2,"readiness":"completion","project_to_github":True}))
fail(lambda x:x["edges"].append({"blocker":1,"blocked":1,"readiness":"completion","project_to_github":True}))
fail(lambda x:x["edges"][0].update(project_to_github=True))
fail(lambda x:x["edges"].append(copy.deepcopy(x["edges"][0])))
fail(lambda x:x["edges"][0].update(blocker=99))
print("github-issue-dag selftest: PASS (positive=4 mutations=5 live=NOT_EXERCISED)")
