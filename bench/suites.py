"""Run a repository's test suites inside a container and reduce them to {repo-relative file: passed|failed}."""
import json
import xml.etree.ElementTree as ET

WORKSPACE = "/workspace/"


def _rel(path):
    return path[len(WORKSPACE):] if path.startswith(WORKSPACE) else path


def parse_vitest(text):
    data = json.loads(text)
    return {_rel(r["name"]): ("passed" if r["status"] == "passed" else "failed") for r in data["testResults"]}


def parse_junit(text, cwd):
    statuses = {}
    for case in ET.fromstring(text).iter("testcase"):
        file = case.get("file") or case.get("classname", "").rsplit(".", 1)[0].replace(".", "/") + ".py"
        rel = f"{cwd}/{file}".lstrip("./") if cwd not in ("", ".") else file
        failed = any(child.tag in ("failure", "error") for child in case)
        if failed or rel not in statuses:
            statuses[rel] = "failed" if failed else statuses.get(rel, "passed")
    return statuses


def parse_perfile(text, cwd):
    statuses = {}
    for line in text.splitlines():
        status, _, path = line.partition(" ")
        if status in ("passed", "failed") and path:
            path = path[2:] if path.startswith("./") else path
            statuses[path if cwd in ("", ".") else f"{cwd}/{path}"] = status
    return statuses


def script_for(suite, out):
    """perfile suites name a `list` command printing test files (relative to cwd); each file runs alone via `cmd`."""
    if suite["format"] == "perfile":
        return (f"cd /workspace/{suite['cwd']} && ({suite['list']}) > {out}.files 2> {out}.log; "
                f"while IFS= read -r f; do if timeout 300 {suite['cmd']} \"$f\" >> {out}.log 2>&1; "
                f"then echo \"passed $f\"; else echo \"failed $f\"; fi; done < {out}.files > {out}; echo rc=$?")
    if suite["format"] == "vitest":
        tail = f"--reporter=json --outputFile={out}"
    elif suite["format"] == "pytest":
        tail = f"--junitxml={out} -o junit_family=xunit1"
    else:
        raise ValueError(suite["format"])
    return f"cd /workspace/{suite['cwd']} && {suite['cmd']} {tail} > {out}.log 2>&1; echo rc=$?"


def parse(suite, text):
    if suite["format"] == "vitest":
        return parse_vitest(text)
    if suite["format"] == "perfile":
        return parse_perfile(text, suite["cwd"])
    return parse_junit(text, suite["cwd"])


def run_suites(container, suites, timeout=900):
    statuses, errors = {}, []
    for i, suite in enumerate(suites):
        out = f"/tmp/suite-{i}.out"
        container.exec(f"rm -f {out}; " + script_for(suite, out), timeout=timeout)
        text = container.read(out)
        if not text:
            errors.append({"suite": suite["name"], "log": (container.read(out + ".log") or "")[-1500:]})
            continue
        statuses.update(parse(suite, text))
    return statuses, errors
