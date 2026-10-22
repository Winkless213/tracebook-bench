"""Every shell command in which the agent tried to reach a remote host, and whether the sandbox blocked it.

The proxy allows the model API's host, and the DeepSeek Search/Fetch API lives on that same host, so a run that
calls it could read the web; this audit is how such a run would be found.
"""
import json
import re
import sys
from pathlib import Path

NETWORK = re.compile(r"tools/(search|fetch)|DEEPSEEK_API_KEY|\bcurl\b|\bwget\b|git (clone|fetch|pull|ls-remote)|"
                     r"npm (view|info|install|i)\b|pip3? (install|download)", re.I)
SEARCH_API = re.compile(r"tools/(search|fetch)|DEEPSEEK_API_KEY")
BLOCKED = re.compile(r"CONNECT tunnel failed, response 403|tunneling socket|Could not resolve host|EAI_AGAIN|ENOTFOUND|"
                     r"ECONNREFUSED|Network is unreachable|E403", re.I)


def network_attempts(events_text):
    pending, attempts = {}, []
    for line in events_text.splitlines():
        if not line.startswith("{"):
            continue
        ev = json.loads(line)
        if ev.get("type") == "tool_execution_start" and ev.get("toolName") == "bash":
            command = (ev.get("args") or {}).get("command", "")
            if NETWORK.search(command):
                pending[ev.get("toolCallId")] = command
        elif ev.get("type") == "tool_execution_end" and ev.get("toolCallId") in pending:
            command = pending.pop(ev["toolCallId"])
            output = "".join(b.get("text", "") for b in (ev.get("result") or {}).get("content", []) if isinstance(b, dict))
            attempts.append({"command": command, "blocked": bool(BLOCKED.search(output)),
                             "search_api": bool(SEARCH_API.search(command)), "output": output[:300]})
    return attempts


if __name__ == "__main__":
    runs = sorted(Path(sys.argv[1]).glob("*/events.jsonl"))
    total = blocked = search = 0
    for path in runs:
        for a in network_attempts(path.read_text(encoding="utf-8")):
            total, blocked, search = total + 1, blocked + a["blocked"], search + a["search_api"]
            if not a["blocked"] or a["search_api"]:
                print(path.parent.name, json.dumps(a, ensure_ascii=False))
    print(f"{len(runs)} runs, {total} network attempts, {blocked} blocked, {search} touched the Search/Fetch API")
