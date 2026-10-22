"""Freeze the task set: a sha256 per task directory, and one for the whole list (see PREREGISTRATION.md)."""
import hashlib
import json
import sys
from pathlib import Path


def task_hash(d):
    h = hashlib.sha256()
    for p in sorted(p for p in d.rglob("*") if p.is_file()):
        h.update(p.relative_to(d).as_posix().encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()


def freeze(dirs):
    tasks = []
    for d in map(Path, dirs):
        task = json.loads((d / "task.json").read_text(encoding="utf-8"))
        if task["validation"]["valid"] and not task.get("excluded") and (d / "instruction.md").exists():
            tasks.append({"id": task["id"], "repo": task["repo"], "precedent": task["precedent"]["level"],
                          "sha256": task_hash(d)})
    return sorted(tasks, key=lambda t: t["id"])


if __name__ == "__main__":
    out, dirs = sys.argv[1], sys.argv[2:]
    text = json.dumps({"tasks": freeze(dirs)}, ensure_ascii=False, indent=1) + "\n"
    Path(out).write_text(text, encoding="utf-8", newline="\n")
    print(hashlib.sha256(text.encode("utf-8")).hexdigest())
