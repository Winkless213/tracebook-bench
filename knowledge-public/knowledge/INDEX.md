# 开发知识入口

用途：供 Codex / Claude 按当前开发项目读取代码知识，无需在网页中提问。

1. 按当前工作区的 Git remote 匹配下表仓库，先读对应 CODEBASE.md。
2. 按任务读取 MODULES.md 的相关部分，再打开引用的源码；不要一次加载所有项目。
3. 对照知识文件的 commit 与当前工作区；版本不一致时重新核对相关代码。
4. 这些文件来自代码静态归纳，不能证明测试通过或线上状态；未关联的会话不能当作该项目历史。

5. 接续历史任务时，按需读 SESSIONS.md 与 SESSION-TOPICS.md；历史决定、候选经验与未决问题分别使用。

| GitHub 仓库 | 默认分支 | 已拉取提交 | 代码知识 | 会话知识 |
|---|---|---|---|---|
| [container-loading-planner](https://github.com/Winkless213/container-loading-planner) | `master` | `ee4bd9325b44` | [23 个文本文件已归纳](container-loading-planner/CODEBASE.md) | 本组不提供 |

当前：21 个仓库已发现，21 个已拉取；19 个项目 Markdown 已生成并通过来源检查。

处理方式：[Repomix 1.18.1](https://github.com/yamadashy/repomix) 进行代码整理和敏感信息检查，由配置的强模型归纳。各批实际模型、推理强度、排除文件及用量见各项目 provenance.json。
原始检出与文件清单见 [GitHub 拉取记录](../evidence/github-checkouts.json)。
