import shutil

import pytest

from bench.container import Container
from bench.run import VERIFY_PREP, is_infra_failure, judge, prepare_script, suites_to_run

TASK = {"hidden_tests": ["apps/a/x.spec.ts"]}


def test_an_empty_final_answer_is_an_infra_failure():
    metrics = {"assistant_messages": 13, "turns": 13, "last_stop_reason": "stop", "last_empty": True}
    assert is_infra_failure(metrics)
    assert not is_infra_failure(metrics | {"last_empty": False})


def test_resolved_needs_every_f2p_green_and_no_p2p_broken():
    validation = {"f2p": ["a.spec.ts"], "p2p": ["b.spec.ts"]}
    assert judge({"a.spec.ts": "passed", "b.spec.ts": "passed"}, validation)["resolved"]
    assert not judge({"a.spec.ts": "passed", "b.spec.ts": "failed"}, validation)["resolved"]
    assert judge({"b.spec.ts": "passed"}, validation)["f2p_failed"] == ["a.spec.ts"]


def test_only_the_none_condition_strips_context_files():
    assert "AGENTS.md" in prepare_script(TASK, "none", "https://example.invalid/r.git")
    assert "AGENTS.md" not in prepare_script(TASK, "agents_md", "https://example.invalid/r.git")
    assert "rm -f apps/a/x.spec.ts" in prepare_script(TASK, "tb_skill", "https://example.invalid/r.git")


AGENT_EDITS = """cd /workspace
echo fixed > src/a.ts
echo new > src/new.ts
echo weakened > test/x.test.ts
rm src/b.test.ts
echo mine > src/c.test.ts
git mv -f test/y.test.ts test/z.test.ts
"""


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_verify_prep_keeps_source_changes_and_reverts_test_changes():
    setup = ("set -e\nmkdir -p /workspace/src /workspace/test /bench\ncd /workspace\n"
             "echo a > src/a.ts; echo b > src/b.test.ts; echo x > test/x.test.ts; echo y > test/y.test.ts\n"
             "git init -q; git add -A; git commit -qm snapshot\n")
    check = ("cat src/a.ts src/new.ts src/b.test.ts test/x.test.ts test/y.test.ts\n"
             "ls src/c.test.ts test/z.test.ts 2>&1 | grep -c 'No such file'\ngrep -c '^diff --git' /bench/agent.diff\n")
    with Container("tb-agent-base") as c:
        rc, out = c.exec(setup + AGENT_EDITS + VERIFY_PREP + check, timeout=120)
    assert out.split() == ["verify-ready", "fixed", "new", "b", "x", "y", "2", "6"]  # the rename is one diff entry


SUITES = [{"name": "server", "cwd": "apps/server"}, {"name": "admin", "cwd": "apps/admin"}]


def test_only_suites_touched_by_the_change_or_the_f2p_files_run():
    run = suites_to_run(SUITES, ["apps/admin/src/a.ts"], ["apps/admin/src/a.test.ts"])
    assert [s["name"] for s in run] == ["admin"]
    assert [s["name"] for s in suites_to_run(SUITES, [], ["apps/server/test/x.spec.ts"])] == ["server"]


def test_a_change_outside_every_suite_runs_them_all():
    assert len(suites_to_run(SUITES, ["packages/shared/index.ts"], ["apps/admin/src/a.test.ts"])) == 2


def test_p2p_in_suites_that_did_not_run_is_not_counted_as_broken():
    validation = {"f2p": ["apps/admin/a.test.ts"], "p2p": ["apps/server/b.spec.ts"]}
    assert judge({"apps/admin/a.test.ts": "passed"}, validation, ["apps/admin"])["resolved"]
    assert not judge({"apps/admin/a.test.ts": "passed"}, validation, ["apps/admin", "apps/server"])["resolved"]
