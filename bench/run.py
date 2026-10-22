"""Run (task x condition x attempt) in throwaway containers and record verified outcomes."""
import argparse
import json
import os
import random
import shlex
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bench.agent import CONDITIONS, KNOWLEDGE_CONDITIONS, knowledge_use, parse_events, pi_script, settings_json
from bench.container import Container
from bench.images import image_name
from bench.paths import TEST_PATH
from bench.suites import run_suites

PROMPT = """你正在 /workspace 仓库里工作。请修复下面这个问题。

{issue}

完成标准：问题被修复，且不破坏现有功能。可以阅读代码、运行测试；不要修改与问题无关的文件。完成后用一两句话说明改动。
"""
ALWAYS_HEADER = "# 本仓库的项目知识索引（Tracebook 由源码归纳生成，修改前以真实源码为准）\n\n"
CONTEXT_CLEANUP = ("find . -name node_modules -prune -o \\( -name AGENTS.md -o -name CLAUDE.md -o -name AGENTS.override.md \\) "
                   "-type f -print0 | xargs -0 rm -f; rm -rf .claude .codex .agents .pi")
TEST_GREP = shlex.quote(TEST_PATH.pattern)
LOCK = threading.Lock()


def prepare_script(task, condition, remote):
    lines = ["set -e", "cd /workspace", "git apply --whitespace=nowarn /bench/task/regression.patch"]
    lines += [f"rm -f {shlex.quote(f)}" for f in task["hidden_tests"]]
    if condition == "none":
        lines.append(CONTEXT_CLEANUP)
    # D:/ is the npm cache dir from the repo's Windows .npmrc, created under whatever directory npm runs in
    lines += ["git init -q", "printf 'D:/\\n' >> .git/info/exclude", "git add -A", "git commit -qm snapshot",
              f"git remote add origin {shlex.quote(remote)}", "git config remote.origin.pushurl no-push://disabled",
              "echo prepared"]
    return "\n".join(lines)


def _under(path, cwd):
    return cwd in ("", ".") or path.startswith(cwd.rstrip("/") + "/")


def suites_to_run(suites, changed, f2p):
    """Suites holding an f2p file or an agent change; every suite when a change lies outside all of them."""
    if any(not any(_under(p, s["cwd"]) for s in suites) for p in changed):
        return list(suites)
    return [s for s in suites if any(_under(p, s["cwd"]) for p in [*changed, *f2p])]


VERIFY_PREP = f"""cd /workspace
git add -A
git diff --cached HEAD > /bench/agent.diff
git diff --cached --no-renames --name-only HEAD | grep -E {TEST_GREP} > /tmp/touched-tests || true
while IFS= read -r f; do
  if git cat-file -e "HEAD:$f" 2>/dev/null; then git checkout HEAD -- "$f"; else git rm -q --cached -- "$f"; rm -f -- "$f"; fi
done < /tmp/touched-tests
git diff --cached --no-renames --name-only HEAD > /bench/changed.txt
echo verify-ready
"""


def judge(statuses, validation, ran_cwds=("",)):
    f2p_failed = [f for f in validation["f2p"] if statuses.get(f) != "passed"]
    p2p = [f for f in validation["p2p"] if any(_under(f, c) for c in ran_cwds)]
    p2p_broken = [f for f in p2p if statuses.get(f) != "passed"]
    return {"resolved": not f2p_failed and not p2p_broken, "f2p_failed": f2p_failed, "p2p_broken": p2p_broken}


def is_infra_failure(metrics):
    # An answer with neither text nor a tool call is the API returning an empty response; Pi takes it as the end
    return (metrics["assistant_messages"] == 0 or (metrics["last_stop_reason"] == "error" and metrics["turns"] <= 1)
            or metrics["last_empty"])


def run_one(task_dir, task, repo, condition, attempt, args, key):
    run_id = f"{task['id']}__{condition}__{attempt}"
    out_dir = Path(args.runs) / run_id
    mounts = []
    if condition in KNOWLEDGE_CONDITIONS:
        view = args.code_snapshot if condition == "tb_code" else args.snapshot
        mounts = [(f"{view}/knowledge", "/knowledge"), (f"{view}/skills", "/skills")]
    started = time.time()
    with Container(image_name(task["repo"]), network="tb-internal", env_names=["DEEPSEEK_API_KEY"], mounts=mounts,
                   cpus=args.cpus) as c, tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        c.exec("mkdir -p /bench/task /pi-agent")
        c.cp_in(task_dir / "regression.patch", "/bench/task/regression.patch")
        rc, out = c.exec(prepare_script(task, condition, repo["remote"]))
        if "prepared" not in out:
            raise RuntimeError(f"{run_id}: prepare failed: {out[-800:]}")
        issue = (task_dir / "instruction.md").read_text(encoding="utf-8").strip()
        (tmp / "prompt.md").write_text(PROMPT.format(issue=issue), encoding="utf-8", newline="\n")
        (tmp / "settings.json").write_text(json.dumps(settings_json(args.model, args.thinking)), encoding="utf-8")
        c.cp_in(tmp / "prompt.md", "/bench/prompt.md")
        c.cp_in(tmp / "settings.json", "/pi-agent/settings.json")
        if condition == "tb_always":
            codebase = Path(args.snapshot, "knowledge", task["repo"], "CODEBASE.md").read_text(encoding="utf-8")
            (tmp / "always.md").write_text(ALWAYS_HEADER + codebase, encoding="utf-8", newline="\n")
            c.cp_in(tmp / "always.md", "/bench/always.md")
        agent_start = time.time()
        rc, out = c.exec(pi_script(condition, args.model, args.thinking, args.timeout), timeout=args.timeout + 120)
        agent_secs = time.time() - agent_start
        events = (c.read("/bench/events.jsonl") or "").replace(key, "***")
        stderr = (c.read("/bench/stderr.log") or "").replace(key, "***")
        metrics = parse_events(events)
        c.exec(VERIFY_PREP)
        diff = c.read("/bench/agent.diff") or ""
        changed = (c.read("/bench/changed.txt") or "").split()
        if (task_dir / "hidden").exists():
            c.cp_in(f"{task_dir / 'hidden'}/.", "/workspace/")
        suites = suites_to_run(repo["suites"], changed, task["validation"]["f2p"])
        statuses, suite_errors = run_suites(c, suites)
    verdict = judge(statuses, task["validation"], [s["cwd"] for s in suites])
    record = {"run_id": run_id, "task": task["id"], "repo": task["repo"], "kind": task["kind"],
              "condition": condition, "attempt": attempt, "model": args.model, "thinking": args.thinking,
              "agent_exit": out.strip()[-40:], "agent_secs": round(agent_secs, 1),
              "total_secs": round(time.time() - started, 1), "timed_out": "exit=124" in out,
              "infra_failure": is_infra_failure(metrics),
              "metrics": {k: v for k, v in metrics.items() if k not in ("reads", "bash")},
              "knowledge_use": knowledge_use(metrics), "diff_lines": diff.count("\n"), "changed_files": changed,
              "suites_run": [s["name"] for s in suites], "suite_errors": suite_errors, **verdict}
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in (("events.jsonl", events), ("stderr.log", stderr), ("agent.diff", diff),
                       ("record.json", json.dumps(record, ensure_ascii=False, indent=2))):
        (out_dir / name).write_text(text, encoding="utf-8", newline="\n")
    return record


def done(runs, run_id):
    p = Path(runs) / run_id / "record.json"
    return p.exists() and not json.loads(p.read_text(encoding="utf-8")).get("infra_failure")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", nargs="+", required=True, help="task directories")
    ap.add_argument("--repos", nargs="+", required=True, help="repos.json files")
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", default="deepseek-flash")
    ap.add_argument("--thinking", default="max")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--cpus", default="2.5")
    ap.add_argument("--runs", default="D:/tracebook-bench-work/runs")
    ap.add_argument("--snapshot", default="D:/tracebook-bench-work/knowledge-mount")
    ap.add_argument("--code-snapshot", default="D:/tracebook-bench-work/knowledge-code-mount")
    ap.add_argument("--credential", default="D:/tracebook-bench-work/deepseek.local.json")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    key = json.loads(Path(args.credential).read_text(encoding="utf-8"))["api_key"]
    os.environ["DEEPSEEK_API_KEY"] = key
    repos = {}
    for path in args.repos:
        repos.update(json.loads(Path(path).read_text(encoding="utf-8")))
    jobs = []
    for d in map(Path, args.tasks):
        task = json.loads((d / "task.json").read_text(encoding="utf-8"))
        if task.get("excluded"):
            continue
        for condition in args.conditions:
            for attempt in range(1, args.attempts + 1):
                if not done(args.runs, f"{task['id']}__{condition}__{attempt}"):
                    jobs.append((d, task, repos[task["repo"]], condition, attempt))
    random.Random(args.seed).shuffle(jobs)
    print(f"{len(jobs)} runs queued", flush=True)

    def work(job):
        try:
            r = run_one(*job, args, key)
            line = (f"{r['run_id']} resolved={r['resolved']} infra={r['infra_failure']} turns={r['metrics']['turns']} "
                    f"in={r['metrics']['tokens']['input']} out={r['metrics']['tokens']['output']} secs={r['agent_secs']} kb={r['knowledge_use']['touches']}")
        except Exception as e:  # keep the batch going; the job stays undone and is retried on the next invocation
            line = f"{job[1]['id']}__{job[3]}__{job[4]} ERROR {type(e).__name__}: {str(e)[:300]}"
        with LOCK:
            print(line, flush=True)

    with ThreadPoolExecutor(args.workers) as pool:
        list(pool.map(work, jobs))


if __name__ == "__main__":
    main()
