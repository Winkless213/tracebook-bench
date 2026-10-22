"""Turn a historical fix commit into a regression task at the knowledge commit (PR-mirror style, cf. SWE-smith)."""
import json
import subprocess
from pathlib import Path

from bench.paths import TEST_FILE, TEST_PATH


def git(clone, *args, binary=False):
    p = subprocess.run(["git", "-C", str(clone), "-c", "core.autocrlf=false", *args], capture_output=True, check=True)
    return p.stdout if binary else p.stdout.decode("utf-8", "replace")


def changed_files(clone, sha):
    return [line for line in git(clone, "show", "--name-only", "--format=", sha).splitlines() if line]


def make(clone, repo, base, sha, task_dir):
    files = changed_files(clone, sha)
    src = [f for f in files if not TEST_PATH.search(f)]
    hidden = [f for f in files if TEST_FILE.search(f)]
    hidden = [f for f in hidden if subprocess.run(["git", "-C", str(clone), "cat-file", "-e", f"{base}:{f}"],
                                                  capture_output=True).returncode == 0]
    task_dir = Path(task_dir)
    (task_dir / "hidden").mkdir(parents=True, exist_ok=True)
    (task_dir / "regression.patch").write_bytes(git(clone, "diff", sha, f"{sha}^", "--", *src, binary=True))
    for f in hidden:
        dest = task_dir / "hidden" / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(git(clone, "show", f"{base}:{f}", binary=True))
    subject = git(clone, "log", "-1", "--format=%s", sha).strip()
    spec = {"id": task_dir.name, "repo": repo, "kind": "historical", "source_commit": sha, "base_commit": base,
            "subject": subject, "src_files": src, "hidden_tests": hidden}
    (task_dir / "task.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                                        newline="\n")
    return spec
