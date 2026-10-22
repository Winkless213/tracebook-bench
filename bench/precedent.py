"""Tag each task by whether the mounted knowledge already records its source fix (commit sha or subject line)."""
import json
import re
import sys
from pathlib import Path

CURATED = ("SESSIONS.md", "SESSION-TOPICS.md", "CODEBASE.md", "MODULES.md")


def precedent(task, knowledge_root):
    root = Path(knowledge_root) / task["repo"]
    sha = re.compile(rf"(?<![0-9a-f]){task['source_commit'][:7]}")
    hits = {"sha": [], "subject": []}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in (".md", ".json"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        if sha.search(text):
            hits["sha"].append(rel)
        if task["subject"] in text:
            hits["subject"].append(rel)
    found = set(hits["sha"]) | set(hits["subject"])
    level = "curated" if found & set(CURATED) else "history" if found else "none"
    return {"level": level, "sha_files": len(hits["sha"]), "subject_files": len(hits["subject"]),
            "curated_files": sorted(found & set(CURATED))}


if __name__ == "__main__":
    knowledge_root, dirs = sys.argv[1], sys.argv[2:]
    for d in map(Path, dirs):
        task = json.loads((d / "task.json").read_text(encoding="utf-8"))
        task["precedent"] = precedent(task, knowledge_root)
        (d / "task.json").write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        print(task["id"], json.dumps(task["precedent"], ensure_ascii=False))
