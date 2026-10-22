from bench.validate import classify


def test_task_is_valid_only_when_every_hidden_test_turns_red():
    base = {"a.spec.ts": "passed", "b.spec.ts": "passed", "db.spec.ts": "failed"}
    regressed = {"a.spec.ts": "failed", "b.spec.ts": "passed", "db.spec.ts": "failed"}
    result = classify(base, regressed, ["a.spec.ts"])
    assert result["valid"] is True
    assert result["f2p"] == ["a.spec.ts"]
    assert result["p2p"] == ["b.spec.ts"]
    assert result["env_failed"] == ["db.spec.ts"]
    assert result["visible_red"] == []


def test_task_is_invalid_when_a_hidden_test_still_passes_after_regression():
    base = {"a.spec.ts": "passed", "b.spec.ts": "passed"}
    regressed = {"a.spec.ts": "failed", "b.spec.ts": "passed"}
    assert classify(base, regressed, ["a.spec.ts", "b.spec.ts"])["valid"] is False


def test_hidden_files_that_no_suite_runs_do_not_decide_validity():
    base = {"a.spec.ts": "passed"}
    regressed = {"a.spec.ts": "failed"}
    result = classify(base, regressed, ["a.spec.ts", "test/integration/x.spec.ts"])
    assert result["valid"] is True
    assert result["hidden_not_run"] == ["test/integration/x.spec.ts"]


def test_red_tests_outside_the_hidden_set_are_reported_as_visible():
    base = {"a.spec.ts": "passed", "c.spec.ts": "passed"}
    regressed = {"a.spec.ts": "failed", "c.spec.ts": "failed"}
    result = classify(base, regressed, ["a.spec.ts"])
    assert result["visible_red"] == ["c.spec.ts"]
