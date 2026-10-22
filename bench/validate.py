"""Check that a task is well-formed: suites pass at the base, the regression turns the hidden tests red."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bench.container import Container
from bench.images import image_name
from bench.suites import run_suites

SNAPSHOT = "cd /workspace && git init -q && git add -A && git commit -qm snapshot && echo ok"


def classify(base, regressed, hidden):
    f2p = sorted(f for f, s in regressed.items() if s == "failed" and base.get(f) == "passed")
    p2p = sorted(f for f, s in base.items() if s == "passed" and regressed.get(f) == "passed")
    env_failed = sorted(f for f, s in base.items() if s != "passed")
    hidden_run = [f for f in hidden if f in base]
    hidden_red = [f for f in hidden_run if f in f2p]
    return {"f2p": f2p, "p2p": p2p, "env_failed": env_failed, "hidden_red": hidden_red,
            "hidden_not_run": [f for f in hidden if f not in base],
            "visible_red": [f for f in f2p if f not in hidden],
            "valid": bool(hidden_red) and len(hidden_red) == len(hidden_run)}


def validate(task_dir, repos):
    task_dir = Path(task_dir)
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    suites = repos[task["repo"]]["suites"]
    with Container(image_name(task["repo"])) as c:
        if (task_dir / "hidden").exists():  # synthetic tasks add new test files; historical ones equal the base
            c.cp_in(f"{task_dir / 'hidden'}/.", "/workspace/")
        rc, out = c.exec(SNAPSHOT)
        base, errors = run_suites(c, suites)
        c.cp_in(task_dir / "regression.patch", "/tmp/regression.patch")
        rc, out = c.exec("cd /workspace && git apply --whitespace=nowarn /tmp/regression.patch")
        if rc != 0:
            result = {"valid": False, "reason": "regression patch does not apply", "detail": out[-500:]}
        else:
            regressed, errors2 = run_suites(c, suites)
            result = classify(base, regressed, task["hidden_tests"])
            result["suite_errors"] = errors + errors2
    task["validation"] = result
    (task_dir / "task.json").write_text(json.dumps(task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return task["id"], result


if __name__ == "__main__":
    repos_path, workers, *dirs = sys.argv[1:]
    repos = json.loads(Path(repos_path).read_text(encoding="utf-8"))
    with ThreadPoolExecutor(int(workers)) as pool:
        for tid, r in pool.map(lambda d: validate(d, repos), dirs):
            print(tid, "valid" if r.get("valid") else "INVALID", "f2p", len(r.get("f2p", [])),
                  "hidden_red", r.get("hidden_red"), "visible_red", r.get("visible_red"), r.get("reason", ""),
                  "errors", len(r.get("suite_errors", [])), flush=True)
