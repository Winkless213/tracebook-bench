from bench.report import markdown, summarize, verdict


def record(task, condition, resolved, tokens=100):
    return {"task": task, "condition": condition, "resolved": resolved, "agent_secs": 10, "timed_out": False,
            "metrics": {"tokens": {"input": tokens, "output": 0, "cacheRead": 0, "totalTokens": tokens}, "tools": {"bash": 1},
                        "cost": 0},
            "knowledge_use": {"touches": 1 if condition.startswith("tb") else 0}}


META = {"t1": {"repo": "r", "precedent": "none"}, "t2": {"repo": "r", "precedent": "curated"}}


def test_task_is_the_unit_and_attempts_are_averaged_first():
    records = [record("t1", "agents_md", True), record("t1", "agents_md", False), record("t1", "agents_md", False),
               record("t2", "agents_md", True)]
    s = summarize(records, META)
    assert s["conditions"]["agents_md"]["resolved"] == (1 / 3 + 1) / 2
    assert s["conditions"]["agents_md"]["pass_all"] == 0.5
    assert s["conditions"]["agents_md"]["pass_any"] == 1


def test_contrast_is_paired_on_tasks_run_in_both_conditions():
    records = [record("t1", "tb_skill", True, 300), record("t1", "agents_md", False, 100),
               record("t2", "tb_skill", True, 300)]
    c = summarize(records, META)["contrasts"]["tb_skill-agents_md"]
    assert c["tasks"] == 1 and c["diff"] == 1 and c["token_ratio"] == 3


def test_prompt_tokens_are_uncached_input_plus_cache_hits():
    a = record("t1", "tb_skill", True, 100)
    a["metrics"]["tokens"].update(cacheRead=200, totalTokens=300)
    s = summarize([a, record("t1", "agents_md", True, 100)], META)
    assert s["contrasts"]["tb_skill-agents_md"]["token_ratio"] == 3
    assert s["conditions"]["tb_skill"]["tokens"] == {"prompt": 300, "uncached": 100, "cacheRead": 200, "output": 0}


def test_cost_uses_the_official_off_peak_prices():
    r = record("t1", "agents_md", True, 1_000_000)
    r["metrics"]["tokens"].update(cacheRead=1_000_000, output=1_000_000)
    s = summarize([r], META)
    assert round(s["conditions"]["agents_md"]["cost_cny"], 6) == 5.02
    assert round(s["total_cost_cny"], 6) == 5.02


def test_markdown_tables_carry_every_condition_and_contrast():
    records = [record("t1", "tb_skill", True), record("t1", "agents_md", False)]
    text = markdown(summarize(records, META))
    assert "| `tb_skill` | 100%" in text and "| `agents_md` | 0%" in text
    assert "| `tb_skill-agents_md` | +100.0 pp |" in text


def test_verdict_follows_the_preregistered_rules():
    assert verdict({"low": 0.01, "high": 0.3}, 1.5) == "useful"
    assert verdict({"low": -0.3, "high": -0.01}, 1.0) == "harmful"
    assert verdict({"low": -0.1, "high": 0.2}, 1.25) == "useless_and_costlier"
    assert verdict({"low": -0.1, "high": 0.2}, 1.1) == "not_shown_useful"
