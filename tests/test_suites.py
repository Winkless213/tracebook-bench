import shutil
from pathlib import Path

import pytest

from bench.container import Container
from bench.suites import parse_junit, parse_perfile, parse_vitest, script_for

FIXTURES = Path(__file__).parent / "fixtures"


def test_vitest_statuses_are_keyed_by_repo_relative_file():
    statuses = parse_vitest((FIXTURES / "vitest-sample.json").read_text(encoding="utf-8"))
    assert statuses == {
        "packages/core/test/unit/report.spec.ts": "failed",
        "packages/core/test/unit/parser.spec.ts": "passed",
    }


def test_junit_marks_a_file_failed_when_any_case_fails():
    statuses = parse_junit((FIXTURES / "junit-sample.xml").read_text(encoding="utf-8"), ".")
    assert statuses["tests/test_ok.py"] == "passed"
    assert statuses["tests/test_bad.py"] == "failed"


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_perfile_suite_runs_each_listed_file_alone():
    suite = {"name": "node", "cwd": "pkg", "format": "perfile", "cmd": "node --test",
             "list": "find . -name '*.test.mjs' | sort"}
    setup = ("mkdir -p /workspace/pkg/lib && cd /workspace/pkg && "
             "echo \"import test from 'node:test'; test('ok', () => {});\" > lib/a.test.mjs && "
             "echo \"import test from 'node:test'; test('bad', () => { throw new Error('x'); });\" > lib/b.test.mjs\n")
    with Container("tb-agent-base") as c:
        c.exec(setup + script_for(suite, "/tmp/s.out"), timeout=120)
        text = c.read("/tmp/s.out")
    assert parse_perfile(text, "pkg") == {"pkg/lib/a.test.mjs": "passed", "pkg/lib/b.test.mjs": "failed"}
