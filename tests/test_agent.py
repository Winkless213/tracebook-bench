import json
from pathlib import Path

from bench.agent import KNOWLEDGE_NUDGE, knowledge_use, parse_events, pi_args, pi_script

FIXTURES = Path(__file__).parent / "fixtures"


def test_events_reduce_to_turns_tokens_and_tools():
    m = parse_events((FIXTURES / "pi-events-sample.jsonl").read_text(encoding="utf-8"))
    assert m["turns"] == 3
    assert m["tokens"]["input"] == 4999
    assert m["tokens"]["output"] == 533
    assert m["tokens"]["cacheRead"] == 2944
    assert m["tools"] == {"bash": 2}
    assert m["settled"] is True
    assert m["last_stop_reason"] == "stop"


def test_a_last_answer_with_only_thinking_is_flagged_empty():
    sample = (FIXTURES / "pi-events-sample.jsonl").read_text(encoding="utf-8")
    assert parse_events(sample)["last_empty"] is False
    usage = {"input": 1, "output": 0, "cacheRead": 0, "cacheWrite": 0, "totalTokens": 1}
    message = {"role": "assistant", "content": [{"type": "thinking", "thinking": "..."}], "usage": usage,
               "stopReason": "stop"}
    assert parse_events(sample + json.dumps({"type": "message_end", "message": message}))["last_empty"] is True


def test_only_the_knowledge_conditions_expose_tracebook():
    assert "--skill" not in pi_args("agents_md", "m", "high")
    assert "--skill" in pi_args("tb_skill", "m", "high")
    assert "--skill" in pi_args("tb_code", "m", "high")
    assert "--append-system-prompt" in pi_args("tb_always", "m", "high")
    assert "--no-context-files" in pi_args("none", "m", "high")
    assert "--no-context-files" not in pi_args("tb_skill", "m", "high")


def test_skill_conditions_carry_the_load_instruction():
    for c in ("tb_skill", "tb_code"):
        args = pi_args(c, "m", "high")
        assert args[args.index("--append-system-prompt") + 1] == KNOWLEDGE_NUDGE
    for c in ("none", "agents_md", "tb_always"):
        assert KNOWLEDGE_NUDGE not in pi_args(c, "m", "high")


def test_the_agent_calls_the_official_deepseek_provider():
    args = pi_args("none", "deepseek-flash", "max")
    assert args[args.index("--provider") + 1] == "deepseek"


def test_cost_is_summed_over_answers():
    usage = {"input": 1, "output": 1, "cacheRead": 0, "cacheWrite": 0, "totalTokens": 2, "cost": {"total": 0.25}}
    message = {"role": "assistant", "content": [{"type": "text", "text": "ok"}], "usage": usage, "stopReason": "stop"}
    line = json.dumps({"type": "message_end", "message": message})
    assert parse_events(line + "\n" + line)["cost"] == 0.5


def test_prompt_text_never_passes_through_the_shell():
    script = pi_script("none", "m", "high", 60)
    assert '"$(cat /bench/prompt.md)"' in script


def test_knowledge_use_counts_reads_and_shell_access():
    m = {"reads": ["/skills/developer-project-knowledge/SKILL.md", "/workspace/a.ts"],
         "bash": ["cat /knowledge/fashion-vendure/CODEBASE.md"]}
    use = knowledge_use(m)
    assert use["touches"] == 2
    assert use["SKILL.md"] and use["CODEBASE.md"] and not use["SESSIONS.md"]
