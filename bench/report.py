"""Aggregate run records into the preregistered tables (see PREREGISTRATION.md)."""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean

from bench.agent import CONDITIONS

CONTRASTS = (("tb_skill", "agents_md"), ("tb_code", "agents_md"), ("tb_skill", "tb_code"), ("tb_always", "agents_md"),
             ("agents_md", "none"), ("tb_skill", "none"))


def load_records(runs_dir):
    records = [json.loads(p.read_text(encoding="utf-8")) for p in Path(runs_dir).glob("*/record.json")]
    return [r for r in records if not r["infra_failure"]], sum(r["infra_failure"] for r in records)


def by_task(records, value):
    table = defaultdict(lambda: defaultdict(list))
    for r in records:
        table[r["task"]][r["condition"]].append(value(r))
    return table


def rate(table, condition, tasks):
    return mean(mean(table[t][condition]) for t in tasks)


def paired_bootstrap(table, a, b, tasks, n=10000, seed=7):
    diffs = [mean(table[t][a]) - mean(table[t][b]) for t in tasks]
    rng = random.Random(seed)
    boots = sorted(mean(rng.choices(diffs, k=len(diffs))) for _ in range(n))
    return {"diff": mean(diffs), "low": boots[int(0.025 * n)], "high": boots[int(0.975 * n) - 1], "tasks": len(diffs)}


def tasks_with(table, *conditions):
    return sorted(t for t, row in table.items() if all(row.get(c) for c in conditions))


def verdict(ci, token_ratio):
    if ci["low"] > 0:
        return "useful"
    if ci["high"] < 0:
        return "harmful"
    return "useless_and_costlier" if token_ratio >= 1.2 else "not_shown_useful"


def summarize(records, meta):
    solved = by_task(records, lambda r: r["resolved"])
    tokens = by_task(records, lambda r: r["metrics"]["tokens"]["totalTokens"])
    out = {"conditions": {}, "contrasts": {}, "groups": {}}
    for c in CONDITIONS:
        rs = [r for r in records if r["condition"] == c]
        tasks = tasks_with(solved, c)
        if not tasks:
            continue
        out["conditions"][c] = {
            "runs": len(rs), "tasks": len(tasks), "resolved": rate(solved, c, tasks),
            "pass_all": mean(all(solved[t][c]) for t in tasks), "pass_any": mean(any(solved[t][c]) for t in tasks),
            # Pi's input is the uncached part of the prompt; cacheRead is the part that hit the cache
            "tokens": {"prompt": mean(r["metrics"]["tokens"]["input"] + r["metrics"]["tokens"]["cacheRead"] for r in rs),
                       "uncached": mean(r["metrics"]["tokens"]["input"] for r in rs),
                       "cacheRead": mean(r["metrics"]["tokens"]["cacheRead"] for r in rs),
                       "output": mean(r["metrics"]["tokens"]["output"] for r in rs)},
            "cost_usd": mean(r["metrics"]["cost"] for r in rs),
            "agent_secs": mean(r["agent_secs"] for r in rs), "timeouts": sum(r["timed_out"] for r in rs),
            "tool_calls": mean(sum(r["metrics"]["tools"].values()) for r in rs),
            "no_knowledge_touch": mean(r["knowledge_use"]["touches"] == 0 for r in rs)}
    for a, b in CONTRASTS:
        tasks = tasks_with(solved, a, b)
        if tasks:
            ci = paired_bootstrap(solved, a, b, tasks)
            ci["token_ratio"] = rate(tokens, a, tasks) / rate(tokens, b, tasks)
            ci["verdict"] = verdict(ci, ci["token_ratio"])
            out["contrasts"][f"{a}-{b}"] = ci
    for field in ("precedent", "repo"):
        groups = defaultdict(list)
        for t in solved:
            groups[meta[t][field]].append(t)
        out["groups"][field] = {g: {c: rate(solved, c, [t for t in ts if solved[t].get(c)])
                                    for c in CONDITIONS if any(solved[t].get(c) for t in ts)} | {"tasks": len(ts)}
                                for g, ts in sorted(groups.items())}
    return out


def task_meta(task_dirs):
    meta = {}
    for d in map(Path, task_dirs):
        task = json.loads((d / "task.json").read_text(encoding="utf-8"))
        meta[task["id"]] = {"repo": task["repo"], "precedent": task.get("precedent", {}).get("level", "none")}
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    records, infra = load_records(args.runs)
    summary = summarize(records, task_meta(args.tasks)) | {"infra_failures_excluded": infra}
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    print(text)


if __name__ == "__main__":
    main()
