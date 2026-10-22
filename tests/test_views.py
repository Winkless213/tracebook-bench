import json

from bench.views import public_view

INDEX = """# 开发知识入口

| GitHub 仓库 | 默认分支 | 已拉取提交 | 代码知识 | 会话知识 |
|---|---|---|---|---|
| [private-app](https://github.com/u/private-app) | `main` | `aaa` | [x](private-app/CODEBASE.md) | 本组不提供 |
| [open-app](https://github.com/u/open-app) | `main` | `bbb` | [x](open-app/CODEBASE.md) | 本组不提供 |
"""


def test_public_view_keeps_only_the_named_repositories(tmp_path):
    src, dst = tmp_path / "code", tmp_path / "public"
    for repo in ("private-app", "open-app"):
        (src / "knowledge" / repo).mkdir(parents=True)
        (src / "knowledge" / repo / "CODEBASE.md").write_text(repo, encoding="utf-8")
    (src / "knowledge" / "INDEX.md").write_text(INDEX, encoding="utf-8")
    catalog = {"projects": [{"name": "private-app"}, {"name": "open-app"}]}
    (src / "knowledge" / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    (src / "skills" / "s").mkdir(parents=True)
    (src / "skills" / "s" / "SKILL.md").write_text("skill", encoding="utf-8")

    public_view(src, dst, ["open-app"])

    knowledge = dst / "knowledge"
    assert sorted(p.name for p in knowledge.iterdir()) == ["INDEX.md", "catalog.json", "open-app"]
    assert json.loads((knowledge / "catalog.json").read_text(encoding="utf-8")) == {"projects": [{"name": "open-app"}]}
    index = (knowledge / "INDEX.md").read_text(encoding="utf-8")
    assert "open-app" in index and "private-app" not in index and "| GitHub 仓库 |" in index
    assert (dst / "skills" / "s" / "SKILL.md").exists()
