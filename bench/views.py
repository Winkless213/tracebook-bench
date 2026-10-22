"""Derive the knowledge views mounted into containers from a Tracebook knowledge snapshot.

product: everything except generation caches (dot directories).
code:    product minus all session knowledge, leaving only the static code summaries (CODEBASE / MODULES).
public:  a code view restricted to the named public repositories, for publishing.
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
    (root / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    index = (root / "INDEX.md").read_text(encoding="utf-8")
    index = re.sub(r"\| \[\d+ 份会话[^|]*\|$", "| 本组不提供 |", index, flags=re.M)
    (root / "INDEX.md").write_text(index, encoding="utf-8", newline="\n")


def public_view(src, dst, repos):
    root, out = Path(src) / "knowledge", Path(dst) / "knowledge"
    for repo in repos:
        shutil.copytree(root / repo, out / repo)
    shutil.copytree(Path(src) / "skills", Path(dst) / "skills")
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    catalog["projects"] = [p for p in catalog["projects"] if p["name"] in repos]
    (out / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    row = re.compile(r"^\| \[([^\]]+)\]\(")
    lines = [line for line in (root / "INDEX.md").read_text(encoding="utf-8").splitlines(keepends=True)
             if not (m := row.match(line)) or m.group(1) in repos]
    (out / "INDEX.md").write_text("".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    kind, src, dst, *repos = sys.argv[1:]
    if kind == "public":
        public_view(src, dst, repos)
    else:
        {"product": product_view, "code": code_view}[kind](src, dst)
