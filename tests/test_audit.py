import json

from bench.audit import network_attempts


def event(kind, **fields):
    return json.dumps({"type": kind, **fields})


def test_network_commands_are_paired_with_their_output():
    text = "\n".join([
        event("tool_execution_start", toolName="bash", toolCallId="a", args={"command": "git ls-remote origin"}),
        event("tool_execution_start", toolName="bash", toolCallId="b", args={"command": "ls src"}),
        event("tool_execution_end", toolCallId="b", result={"content": [{"type": "text", "text": "app.py"}]}),
        event("tool_execution_end", toolCallId="a", result={"content": [
            {"type": "text", "text": "fatal: CONNECT tunnel failed, response 403"}]}),
        event("tool_execution_start", toolName="bash", toolCallId="c",
              args={"command": "curl https://api.deepseek.com/v1/tools/fetch -d '{}'"}),
        event("tool_execution_end", toolCallId="c", result={"content": [{"type": "text", "text": "{\"content\": \"...\"}"}]}),
    ])
    attempts = network_attempts(text)
    assert [a["command"] for a in attempts] == ["git ls-remote origin", "curl https://api.deepseek.com/v1/tools/fetch -d '{}'"]
    assert [a["blocked"] for a in attempts] == [True, False]
    assert [a["search_api"] for a in attempts] == [False, True]


def test_a_curl_fail_403_counts_as_blocked_but_output_without_a_block_signal_does_not():
    text = "\n".join([
        event("tool_execution_start", toolName="bash", toolCallId="a", args={"command": "curl -f https://example.com/x"}),
        event("tool_execution_end", toolCallId="a", result={"content": [
            {"type": "text", "text": "curl: (22) The requested URL returned error: 403\n"}]}),
        event("tool_execution_start", toolName="bash", toolCallId="b",
              args={"command": "git ls-remote origin 2>&1 | grep 0cb06d3 | head -5; echo exit:$?"}),
        event("tool_execution_end", toolCallId="b", result={"content": [{"type": "text", "text": "exit:0\n"}]}),
    ])
    assert [a["blocked"] for a in network_attempts(text)] == [True, False]
