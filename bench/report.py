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
# DeepSeek official deepseek-flash prices, CNY per 1M tokens, off-peak (2026-10; every run fell in off-peak hours)
PRICE_CNY = {"input": 1.0, "cacheRead": 0.02, "output": 4.0}
VERDICTS = {"useful": "有用", "harmful": "有害", "useless_and_costlier": "没用且更贵", "not_shown_useful": "未证明有用"}


def cost_cny(r):
    return sum(r["metrics"]["tokens"][k] * price for k, price in PRICE_CNY.items()) / 1e6


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
    out = {"conditions": {}, "contrasts": {}, "groups": {}, "total_cost_cny": sum(cost_cny(r) for r in records)}
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
            "cost_cny": mean(cost_cny(r) for r in rs),
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


def pct(x):
    return f"{100 * x:.0f}%"


def markdown(summary):
    """The README tables, rendered from the summary so no number is copied by hand."""
    lines = ["| 组 | 解决率 | 3 次全解 | 至少 1 次 | 完整提示词 | 未缓存 | 输出 | 费用 | 代理耗时 | 工具调用 | 未打开知识 |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, s in summary["conditions"].items():
        t = s["tokens"]
        skipped = pct(s["no_knowledge_touch"]) if c in ("tb_skill", "tb_code") else "—"
        lines.append(f"| `{c}` | {pct(s['resolved'])} | {pct(s['pass_all'])} | {pct(s['pass_any'])} | "
                     f"{t['prompt'] / 1e4:.1f} 万 | {t['uncached'] / 1e4:.1f} 万 | {t['output'] / 1e4:.2f} 万 | "
                     f"{s['cost_cny']:.2f} 元 | {s['agent_secs'] / 60:.1f} 分 | {s['tool_calls']:.0f} | {skipped} |")
    lines += ["", "| 对比 | 差值 | 95% 置信区间 | 题数 | token 比 | 判定 |", "|---|---|---|---|---|---|"]
    for name, ci in summary["contrasts"].items():
        lines.append(f"| `{name}` | {100 * ci['diff']:+.1f} pp | [{100 * ci['low']:+.1f}, {100 * ci['high']:+.1f}] | "
                     f"{ci['tasks']} | {ci['token_ratio']:.2f} | {VERDICTS[ci['verdict']]} |")
    for field, title in (("precedent", "先例标签"), ("repo", "仓库")):
        lines += ["", f"| {title} | 题数 | " + " | ".join(f"`{c}`" for c in CONDITIONS) + " |",
                  "|---|---|" + "---|" * len(CONDITIONS)]
        for group, row in summary["groups"][field].items():
            lines.append(f"| {group} | {row['tasks']} | " + " | ".join(pct(row[c]) if c in row else "—" for c in CONDITIONS)
                         + " |")
    return "\n".join(lines) + "\n"


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
    ap.add_argument("--markdown")
    args = ap.parse_args()
    records, infra = load_records(args.runs)
    summary = summarize(records, task_meta(args.tasks)) | {"infra_failures_excluded": infra}
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
    if args.markdown:
        Path(args.markdown).write_text(markdown(summary), encoding="utf-8", newline="\n")
    print(text)


if __name__ == "__main__":
    main()
