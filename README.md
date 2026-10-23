# Tracebook Bench

给编码代理接上项目知识层，它修 bug 会不会更成功？这个仓库用真实仓库里的回归修复任务回答这个问题，指标和判定规则在正式运行之前写死。

> **English summary.** A preregistered evaluation of whether a project-knowledge layer (Tracebook: code summaries plus redacted session history) helps a coding agent fix real regressions. 31 tasks built from git history and a public repository, 5 context conditions, 3 attempts each (465 runs), Pi coding agent with DeepSeek V4.1 Flash at max reasoning effort. Method, decision rules and deviations are in [PREREGISTRATION.md](PREREGISTRATION.md). **Result:** by the preregistered rules the knowledge layer was "not useful and costlier" in this setting: the primary contrast was +1.1 pp (95% CI [0, +3.2]) at 1.32× the tokens. The benchmark hit a ceiling, though. With no context at all the agent already solved 98%, and 29 of 31 tasks were solved in all 15 runs, so the result does not speak to harder tasks.

## 结论

按事先写下的规则：**在本设置下，知识层没用且更贵。**

- **主要对比 `tb_skill − agents_md`**：解决率 +1.1 个百分点，95% 置信区间 [+0.0, +3.2]，下界没有大于 0；token 多 32%。按判定规则 4 写成"没用且更贵"。
- **拆开看**：代码地图（`tb_code − agents_md`）+0.0 个百分点，token 多 16%；会话记忆（`tb_skill − tb_code`）+1.1 个百分点，区间 [+0.0, +3.2]。两者都没有被证明有用。
- **把 CODEBASE.md 塞进系统提示（`tb_always`）最差**：解决率 −1.1 个百分点，3 次全解的比例 94%，是各组最低；token 是 `agents_md` 的 2.37 倍。
- **知识确实被读了**：`tb_skill` 和 `tb_code` 没有一次运行是没打开知识文件的，所以没有提升不是因为代理不用它。

最重要的一条不在判定规则里：**这批题对这个模型太简单，实验碰到了天花板。** 什么上下文都不给的 `none` 组解决率已经是 98%。31 题里有 29 题在 5 组共 15 次运行中全部解决，失败只出现在 2 道题上，组间差异几乎全来自其中一道（`tb_skill` 3/3，其余组 1–2/3）。所以这个结果只能说明"在这批题和这个模型上，知识层没有可提升的余地"，不能推出"知识层对更难的任务也没用"。

## 测的是什么

Tracebook 把一个仓库整理成两类知识：从源码归纳的代码地图（CODEBASE.md / MODULES.md），以及脱敏后的历史会话和经验（SESSIONS.md 等）。要回答的是：在同一个仓库里修一个真实回归时，给代理这些知识，成功率会不会更高，又要多花多少 token、时间和钱。

## 实验设计

### 任务：31 道回归

| 仓库 | 内容 | 题数 | 先例标签 |
|---|---|---|---|
| fashion-vendure（私有） | TypeScript monorepo：Vendure 电商服务端、管理端和店面 | 26 | curated 11 · history 14 · none 1 |
| trade-copilot（私有） | Python 外贸助手 | 1 | curated 1 |
| container-loading-planner（公开） | Python 装柜规划工具 | 4（合成） | none 4 |

- **构造**：参考 SWE-smith 的 PR-mirror 做法，从 Git 历史里找自带测试的修复提交，在知识层绑定的提交上把修复的非测试改动反向打回去，得到回归；修复改过的测试文件作为隐藏测试。
- **有效性**：隐藏测试在基线上全绿、打回回归后变红，才算有效题。
- **描述**：每题一份中文 issue 式描述，写现象和期望行为，隐藏测试检查的行为边界都写进去，但不写要改的文件、函数或行号。隐藏测试依赖修复中新加的函数名、参数名这类"不指明实现就写不清"的题，在任何运行之前排除（共 7 题）。
- **先例标签**：修复提交的 sha 或标题出现在知识层里，标 `curated`（出现在整理过的知识里）或 `history`（只出现在历史会话里），否则标 `none`。用来区分"知识帮代理读懂了代码"和"知识里本来就记着这次修复"。
- **公开任务**：私有仓库的题目不公开。container-loading-planner 上的 4 题是人工注入的回归，配新写的隐藏测试，让外部可以复现整条流程。

### 对照组

| 组 | 代理能看到的上下文 |
|---|---|
| `none` | 不给任何上下文文件 |
| `agents_md` | 仓库自带的 AGENTS.md |
| `tb_skill` | agents_md + 只读挂载完整知识层，以 skill 告诉代理入口，并加一句加载指令 |
| `tb_code` | 同 tb_skill，但知识层去掉全部会话知识，只剩代码地图 |
| `tb_always` | agents_md + 把 CODEBASE.md 全文放进系统提示 |

`tb_code − agents_md` 衡量代码地图的作用，`tb_skill − tb_code` 衡量会话记忆的作用。

### 代理、判定与隔离

- **代理**：Pi coding agent 1.1.0，模型 DeepSeek V4.1 Flash（官方接口 `deepseek-flash`，推理强度 max）。每次限时 30 分钟，每题每组 3 次，共 465 次，顺序随机打乱。
- **判定**：代理结束后，先还原它对测试文件的改动、删掉它新建的测试文件，再放回隐藏测试跑相关套件。fail-to-pass 全部转绿、pass-to-pass 没有回退，才算解决。
- **隔离**：每次运行使用单提交的仓库快照，看不到 Git 历史里的修复；代理运行期间隐藏测试不存在；容器只能经白名单代理访问模型 API；push 被禁用。

### 预注册

指标、对比方式（在任务层面配对，自助法重抽样 10000 次）和判定规则写在 [PREREGISTRATION.md](PREREGISTRATION.md)，正式运行前写好，任务清单冻结并记下哈希。正式运行前做过的 5 处修改，以及运行中的主机中断和高峰时段计价，都在文末的偏离记录里。

## 结果

465 次运行全部完成，没有因基础设施失败剔除的运行。下表中 token 和费用是每次运行的平均值，解决率先在任务内平均、再对任务平均。

| 组 | 解决率 | 3 次全解 | 至少 1 次 | 完整提示词 | 未缓存 | 输出 | 费用 | 代理耗时 | 工具调用 |
|---|---|---|---|---|---|---|---|---|---|
| `none` | 98% | 97% | 100% | 70.1 万 | 4.1 万 | 0.69 万 | 0.08 元 | 2.4 分 | 26 |
| `agents_md` | 99% | 97% | 100% | 90.0 万 | 2.9 万 | 1.04 万 | 0.09 元 | 3.6 分 | 40 |
| `tb_skill` | 100% | 100% | 100% | 119.0 万 | 4.5 万 | 1.05 万 | 0.11 元 | 3.8 分 | 43 |
| `tb_always` | 98% | 94% | 100% | 215.2 万 | 2.3 万 | 0.95 万 | 0.10 元 | 3.5 分 | 36 |
| `tb_code` | 99% | 97% | 100% | 105.0 万 | 3.8 万 | 1.08 万 | 0.10 元 | 3.5 分 | 42 |

| 对比 | 差值 | 95% 置信区间 | token 比 | 判定 |
|---|---|---|---|---|
| `tb_skill − agents_md`（主要） | +1.1 pp | [+0.0, +3.2] | 1.32 | 没用且更贵 |
| `tb_code − agents_md` | +0.0 pp | [+0.0, +0.0] | 1.16 | 未证明有用 |
| `tb_skill − tb_code` | +1.1 pp | [+0.0, +3.2] | 1.13 | 未证明有用 |
| `tb_always − agents_md` | −1.1 pp | [−3.2, +0.0] | 2.37 | 没用且更贵 |
| `agents_md − none` | +1.1 pp | [+0.0, +3.2] | 1.29 | 没用且更贵 |
| `tb_skill − none` | +2.2 pp | [+0.0, +6.5] | 1.70 | 没用且更贵 |

按先例标签分组：

| 先例标签 | 题数 | `none` | `agents_md` | `tb_skill` | `tb_always` | `tb_code` |
|---|---|---|---|---|---|---|
| curated | 12 | 94% | 97% | 100% | 97% | 97% |
| history | 14 | 100% | 100% | 100% | 98% | 100% |
| none | 5 | 100% | 100% | 100% | 100% | 100% |

`curated` 题上的差异来自同一道题，主要对比没有显著提升，判定规则 5 不适用。

按仓库分组：fashion-vendure 26 题，各组 97%–100%；container-loading-planner 4 题和 trade-copilot 1 题，各组都是 100%。

**代理读了哪些知识**（占该组运行的比例）：

| 文件 | `tb_skill` | `tb_code` |
|---|---|---|
| SKILL.md | 100% | 100% |
| INDEX.md | 87% | 90% |
| CODEBASE.md | 60% | 67% |
| MODULES.md | 69% | 60% |
| SESSIONS.md | 43% | — |
| SESSION-TOPICS.md | 37% | — |
| history/ | 22% | — |

**其他观察**

- AGENTS.md 本身也有代价：和 `none` 相比，代理平均耗时从 2.4 分钟变成 3.6 分钟，工具调用从 26 次变成 40 次，解决率只多 1.1 个百分点。
- 没有运行超时，所有运行都以正常 `stop` 结束。

**隔离审计**（`python -m bench.audit runs`）：465 次运行中，代理共尝试联网 57 次，全部被拦下。其中 55 次的输出里直接有拦截信号。剩下 2 次逐条核对过：一次 `curl` 输出 `000` 并打印 no network，代理日志在这次运行期间有对该域名的拒绝记录；另一次 `git ls-remote` 没有输出，在同一镜像里重放得到的是无法解析主机。没有一次运行调用 DeepSeek 的 Search/Fetch 接口。

**费用**：465 次运行按 DeepSeek 官方闲时价计 45.1 元。正式运行有 128 次运行落在高峰时段（北京时间工作日 9–12 点、14–18 点，按 2 倍计价），实际账单估计约 56 元。表中统一按闲时价计算，见偏离记录 7。

## 试点发现的流水线问题

正式运行前的试点没有计入分析，但它暴露的问题本身值得记录：

1. **API 计数会改变代理的行为。** 试点最初走一个 API 中转站。它把缓存命中重复计入 `input_tokens`，Pi 用这个数估算上下文，并据此限制每轮最多输出多少 token。结果真实提示词到 6 万 token 左右时，输出额度就只剩一两千，代理被截断后直接结束。上下文越大的组越早触发，正好系统性地压低带知识的组。正式运行改用官方接口。
2. **只列出 skill，代理不会去用。** 系统提示里列了 skill 的名字、描述和入口，5 次运行里代理一次都没打开知识文件。照搬作者日常工作流里的一句加载指令之后，验证运行中 3 次都读了。
3. **空回复被当成正常结束。** 中转偶尔返回只有思考、没有正文和工具调用的回复，Pi 当作任务完成，代理一行没改就停了。这类运行记为基础设施失败并重跑。
4. **换行符会破坏哈希。** Windows 上 `Path.write_text` 默认写 CRLF，任务清单按 CRLF 算出的哈希和 Git 里存的 LF 文件对不上，已统一为 LF 后重算。

## 复现（公开部分）

需要 Docker、Python 3.12+ 和一个 DeepSeek API key。下面在公开任务上复现完整流程：

```bash
# 1. 代理基础镜像、白名单代理和隔离网络
docker build -t tb-agent-base docker/agent-base
docker build -t tb-proxy docker/proxy
docker network create --internal tb-internal
docker run -d --name tb-proxy --restart unless-stopped tb-proxy
docker network connect tb-internal tb-proxy

# 2. 仓库镜像，源码固定在知识层绑定的提交
git clone https://github.com/Winkless213/container-loading-planner clones/container-loading-planner
#    构建时会把源码复制到临时目录；系统盘空间不够时，用环境变量 TB_WORK 指向别的目录
python -m bench.images repos.public.json clones container-loading-planner

# 3. 运行；凭据文件内容为 {"api_key": "sk-..."}，不要放进仓库
python -m bench.run --tasks tasks/public/* --repos repos.public.json --runs runs \
  --snapshot knowledge-public --code-snapshot knowledge-public --credential /path/to/deepseek.local.json

# 4. 汇总
python -m bench.report --runs runs --tasks tasks/public/* --out summary.json
```

公开的知识层只有代码地图，不含会话知识，所以在公开任务上 `tb_skill` 与 `tb_code` 看到的内容相同。`python -m bench.validate repos.public.json 2 tasks/public/*` 可以重新验证题目，它会改写各题的 `task.json`。测试用 `python -m pytest tests`，其中几项需要本地已构建 `tb-agent-base`。

## 目录

| 路径 | 内容 |
|---|---|
| `bench/make_task.py`、`validate.py` | 从修复提交构造回归、验证题目 |
| `bench/images.py`、`container.py`、`suites.py` | 仓库镜像、容器操作、测试套件运行与解析 |
| `bench/agent.py`、`run.py` | 各组的 Pi 配置、单次运行与判定 |
| `bench/views.py`、`precedent.py`、`manifest.py` | 知识视图、先例标签、任务清单冻结 |
| `bench/report.py` | 按预注册规则汇总 |
| `tasks/public/` | 4 道公开任务 |
| `knowledge-public/` | container-loading-planner 的代码地图与 skill |
| `docker/` | 代理基础镜像与白名单代理 |

## 局限

- **天花板效应。** `none` 组已经解决 98%，这批题对这个模型区分度太低。预注册时按题数估计能检出约 15 个百分点的差异，但基线接近 100% 时，向上根本没有这么大的空间。
- 只测了一个模型和一个代理框架，结论不一定适用于更强的模型或其他框架。
- 31 题里 26 题来自同一个仓库，结果主要反映这个仓库；按题数估算，只能检出约 15 个百分点以上的差异。
- 私有仓库的题目内容不公开，只公开汇总数字和清单哈希。
- 31 题中有 26 题的修复记录在知识层里（curated 或 history），`tb_code` 组用来拆开这部分影响。
- 题目描述由实验者在知道修复的情况下撰写，可能带有暗示；按"不写文件、函数和行号"的规则约束。
- `tb_skill` / `tb_code` 加了一句加载指令，比较的是"知识 + 让代理使用它的指令"这个整体。
- 公开仓库的 4 题是合成回归，通常比真实回归简单。
- **网络隔离有一个缺口。** 白名单代理放行模型 API 的域名，而 DeepSeek 的 Search/Fetch 接口在同一个域名上，按域名过滤挡不住。实验靠事后审计补这个缺口：检查所有运行的命令，没有一次调用这些接口。
- **运行中断过一次。** 正式运行进行到一半时，主机内存不足，接着睡眠后没有正常恢复。之后用同一份清单、同一批镜像、同样的顺序续跑，已完成的运行没有重跑，见偏离记录 6。

## 许可证

MIT，见 [LICENSE](LICENSE)。
