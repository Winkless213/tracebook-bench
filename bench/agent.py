"""Pi configuration, command line per condition, and reduction of its JSONL event stream to run metrics."""
import json
import shlex

PROVIDER = "deepseek"  # Pi's built-in provider for the official API; models and limits come from its catalog
PROXY = "http://tb-proxy:8888"
CONDITIONS = ("none", "agents_md", "tb_skill", "tb_always", "tb_code")
KNOWLEDGE_CONDITIONS = ("tb_skill", "tb_always", "tb_code")
# The user's own global rule that makes agents load this skill (CLAUDE.md rule 33), with Pi's way of loading a skill
KNOWLEDGE_NUDGE = ("开发匹配仓库时先读取 developer-project-knowledge skill 的 SKILL.md 加载它，核实真实目录与 Git 身份，"
                   "按任务读知识和经验，再核对当前源码。资料缺失时直接读代码，不因知识缺口停工；历史结论不等于当前验证。")


def settings_json(model, thinking):
    return {"defaultProvider": PROVIDER, "defaultModel": model, "defaultThinkingLevel": thinking,
            "httpProxy": PROXY, "retry": {"enabled": True, "maxRetries": 4, "baseDelayMs": 3000},
            "compaction": {"enabled": True}, "cacheWarming": "off", "quietStartup": True}


PI_ENV = "PI_CODING_AGENT_DIR=/pi-agent PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 PI_TELEMETRY=0"


def pi_script(condition, model, thinking, timeout_s):
    """Shell line for the container. The prompt is read from a file so the shell never expands its text."""
    args = " ".join(shlex.quote(a) for a in pi_args(condition, model, thinking))
    return (f"cd /workspace && env {PI_ENV} timeout {timeout_s} {args} -- \"$(cat /bench/prompt.md)\" "
            f"> /bench/events.jsonl 2> /bench/stderr.log; echo exit=$?")


def pi_args(condition, model, thinking):
    if condition not in CONDITIONS:
        raise ValueError(condition)
    args = ["pi", "--mode", "json", "--no-session", "--offline", "--no-approve", "--no-extensions", "--no-mcp",
            "--no-prompt-templates", "--no-themes", "--no-skills", "--provider", PROVIDER, "--model", model,
            "--thinking", thinking]
    if condition == "none":
        args.append("--no-context-files")
    if condition in ("tb_skill", "tb_code"):
        args += ["--skill", "/skills/developer-project-knowledge", "--append-system-prompt", KNOWLEDGE_NUDGE]
    if condition == "tb_always":
        args += ["--append-system-prompt", "/bench/always.md"]
    return args


def _usage(message):
    u = message.get("usage") or {}
    return {k: u.get(k, 0) or 0 for k in ("input", "output", "cacheRead", "cacheWrite", "totalTokens")}


def parse_events(text):
    m = {"turns": 0, "assistant_messages": 0, "tokens": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0,
         "totalTokens": 0}, "cost": 0.0, "tools": {}, "tool_errors": 0, "retries": 0, "compactions": 0, "settled": False,
         "last_stop_reason": None, "last_empty": False, "error": None, "reads": [], "bash": [], "final_text": ""}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = ev.get("type")
        if kind == "turn_end":
            m["turns"] += 1
        elif kind == "message_end" and ev.get("message", {}).get("role") == "assistant":
            msg = ev["message"]
            m["assistant_messages"] += 1
            for k, v in _usage(msg).items():
                m["tokens"][k] += v
            m["cost"] += ((msg.get("usage") or {}).get("cost") or {}).get("total", 0) or 0
            m["last_stop_reason"] = msg.get("stopReason")
            m["last_empty"] = not any(b.get("type") in ("text", "toolCall") for b in msg.get("content") or [])
            if msg.get("errorMessage"):
                m["error"] = msg["errorMessage"][:300]
            texts = [b.get("text", "") for b in msg.get("content") or [] if b.get("type") == "text"]
            if texts:
                m["final_text"] = "\n".join(texts)[-1500:]
        elif kind == "tool_execution_start":
            name = ev.get("toolName")
            m["tools"][name] = m["tools"].get(name, 0) + 1
            args = ev.get("args") or {}
            if name == "read":
                m["reads"].append(args.get("path") or args.get("file_path") or "")
            elif name == "bash":
                m["bash"].append((args.get("command") or "")[:300])
        elif kind == "tool_execution_end" and ev.get("isError"):
            m["tool_errors"] += 1
        elif kind == "auto_retry_start":
            m["retries"] += 1
        elif kind == "compaction_start":
            m["compactions"] += 1
        elif kind == "agent_settled":
            m["settled"] = not ev.get("aborted", False)
    return m


def knowledge_use(metrics):
    """Which Tracebook artifacts the agent opened, via the read tool or shell commands."""
    touched = [p for p in metrics["reads"] if "/knowledge/" in p or "/skills/" in p]
    touched += [c for c in metrics["bash"] if "/knowledge" in c or "/skills/" in c]
    kinds = {k: any(k in t for t in touched) for k in ("SKILL.md", "INDEX.md", "CODEBASE.md", "MODULES.md",
                                                         "SESSIONS.md", "SESSION-TOPICS.md", "history/")}
    return {"touches": len(touched), **kinds}
