"""Derive the knowledge views mounted into containers from a Tracebook knowledge snapshot.

product: everything except generation caches (dot directories).
code:    product minus all session knowledge, leaving only the static code summaries (CODEBASE / MODULES).
"""
import json
import re
import shutil
import sys
from pathlib import Path

SESSION_FILES = re.compile(r"^(SESSIONS\.md|SESSION-TOPICS\.md|SESSION-INDEX\.md|history|history-.*\.json|session-topics\.json)$")
CODE_DOCUMENTS = ("CODEBASE.md", "MODULES.md")


def product_view(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".*"))


def code_view(src, dst):
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n.startswith(".") or SESSION_FILES.match(n)])
    root = Path(dst) / "knowledge"
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    for project in catalog["projects"]:
        project["documents"] = [d for d in project.get("documents", []) if d in CODE_DOCUMENTS]
        project["history_status"] = "excluded"
    (root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    index = (root / "INDEX.md").read_text(encoding="utf-8")
    index = re.sub(r"\| \[\d+ 份会话[^|]*\|$", "| 本组不提供 |", index, flags=re.M)
    (root / "INDEX.md").write_text(index, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    kind, src, dst = sys.argv[1:4]
    {"product": product_view, "code": code_view}[kind](src, dst)
