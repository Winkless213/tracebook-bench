> 仓库：https://github.com/Winkless213/container-loading-planner.git · 分支：`master` · 提交：`ee4bd9325b440246b78b0cc604a253e66ade7da7`
> 归纳模型：gpt-6-astra / high；输入：Repomix 整理的源码正文及文档，共 23 个文本文件。
> 这是该提交的静态开发参考；改代码前应读取对应源码。未执行测试或核验线上状态。

# container-loading-planner 代码知识

## 资料范围与用途

本文仅依据本批提供的源码、配置、测试和文档整理，不把资料清单视为仓库完整性证明；未执行启动、测试或打包命令。

项目是本地单机装柜规划工作台：清单输入 → 启发式初稿 → SVG 人工调整 → 规则校验 → 文件交付。实际执行入口是 Python/FastAPI，浏览器承载编辑状态；不是云端协作系统，也不是保证最优或提供工程安全认证的求解器。当前规则采用轴对齐长方体、静态支撑与简化重量分布模型。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py)

- 手工填表、导入、排柜、校验与文件导出不依赖 AI；图片/文字提取调用外部 DashScope，项目实现的是请求、JSON 解析及字段校验，不是自有 OCR 或语言模型。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)
- 浏览器编辑器只有俯视、侧视两种投影；PNG 中有 Matplotlib 绘制的静态 3D 效果图，不等同于交互式 3D 编辑。Three.js、轴荷估算、危险品隔离、PDF 等出现在规划中，不能当作已实现功能。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [_visualizer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_visualizer.py) [PRODUCT_PLAN.md](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/PRODUCT_PLAN.md)

## 入口与模块关系

| 文件 | 实际职责与开发定位 |
|---|---|
| `app.py` | `app = FastAPI(...)`、请求模型、所有 HTTP 路由、清单解析、OOXML 工作簿生成、统计、安全摘要、未锁定重排、AI 调用、启动逻辑。后端业务集中在此文件。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| `_frontend.py` | 单个 Python 原始字符串 `INDEX_HTML` 包含 HTML/CSS/原生 JavaScript；无独立前端构建链。全局 `state`、画布、交互、层内重排、项目存取、草稿、CSV/HTML 导出均在此。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) |
| `_packer.py` | `SKU`、`PlacedItem`、柜型常量、方向枚举、网格启发式、compact/grouped/auto 调度、柜型推荐函数。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) |
| `_validator.py` | `ValidationIssue`、支撑面积并集、累计上压、碰撞、数量、门口区、分段限重、重心偏载等统一校验；依赖 `_packer` 数据类。[_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py) |
| `_visualizer.py` | `Agg` 无窗口渲染、中文字体选择、静态三视图 PNG；由 `app.py` 延迟导入。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_visualizer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_visualizer.py) |
| `preflight.py` / `browser_smoke.py` / `text_quality.py` | 编译与验收编排、真实 Chromium 冒烟、UTF-8/常见乱码扫描。[preflight.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/preflight.py) [browser_smoke.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/browser_smoke.py) [text_quality.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/text_quality.py) |
| `build.bat` / `ContainerPack.spec` | Windows 单文件打包；注意脚本会删除现有 spec，再用命令行重新生成，不能只修改 spec 就期待脚本保留变更。[build.bat](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/build.bat) [ContainerPack.spec](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/ContainerPack.spec) |

`python app.py` 调用 `main()`，从 17283 起尝试 50 个本机端口，延迟打开浏览器，Uvicorn 绑定 `127.0.0.1`。首页 GET `/` 返回 `_frontend.INDEX_HTML` 并显式声明 UTF-8。冻结运行时使用 `sys._MEIPASS` 定位资源。当前路由没有登录、权限或服务端项目存储，不应直接按多用户公网服务部署来理解。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)

## 核心数据与接口

### 数据约定

- 长度和坐标单位是 cm，重量是 kg，体积换算为 m³；X 沿柜长，门在 X 最大端，Z 为高度。侧视 SVG 的屏幕 Y 是 `柜高 - (z + 箱高)`。前端与 `_packer.py` 各自保存一份四种柜型尺寸/限重，修改柜型必须同步。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [_visualizer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_visualizer.py)
- 前端清单使用 `sku/L/W/H/kg/qty/maxTop/mode/side`，`skuPayload()` 转为后端 `model/length/width/height/weight/qty/max_top_load_kg/allow_stack/flat_stack/upright_only`；`side` 与 `upright_only` 取反。清单备注留在前端项目中，不进入排柜 SKU 请求。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)
- `PlacedItem` 保存 SKU、实例号、坐标、实际摆放尺寸、重量、颜色、旋转标记，没有 `locked`；锁定属于 HTTP/前端层，`_placements_from_payload()` 会剥离它。身份匹配广泛使用 `(sku_model, instance_id)`，数组顺序同时被当作装柜回放/导出顺序。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- 输入上限：200 行 SKU、每 SKU 1000 箱、总计 2000 箱、单边 1500 cm、单箱 30000 kg、门口预留 0–600 cm；分段/上压限值最高 1000000 kg，0 表示不限制。`MAX_TOTAL_WEIGHT_KG` 用于规则参数上限，并非清单总重量汇总限制。多数方案请求禁止额外字段，提取结果则忽略额外字段并允许缺失值为 0。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)

### HTTP 路由

| 接口 | 输入/输出与边界 |
|---|---|
| POST `/api/pack` | 清单、柜型、模式、规则 → placements、validation、stats、PNG base64、render_error。先减去门口预留再排柜，用原始柜型做最终校验和统计。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| POST `/api/validate_plan` | 清单 + placements + 规则 → validation；不修改方案，不返回统计。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| POST `/api/repack_unlocked` | 清单 + locked_placements + 规则 → 保留锁定箱的完整新方案、校验、统计；无 pack_mode 参数。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| POST `/api/render_plan` | 人工方案 → PNG、校验、统计；有校验错误也不阻止渲染。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| POST `/api/export_workbook` | 人工方案、项目信息、活动日志、人工复核标记 → XLSX base64、文件名、校验、统计、安全摘要。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| POST `/api/import_manifest` | multipart 文件 → 规范化 skus、逐行 issues、summary。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| GET `/api/import_template` | 三页模板：空白货物清单、字段说明、填写示例。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |
| POST `/api/extract`、`/api/extract_text` | 图片或文本 → DashScope → 解析 JSON → `ExtractedSKUPayload` → skus 和模型名。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) |

`recommend_best_container()` 在算法模块中真实存在，逐柜型尝试后选择容量最小且能全装下的柜型；虽然被 `app.py` 导入，但没有对应 HTTP 路由或当前前端入口。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)

## 主要数据流与算法边界

### 1. 清单输入

手工输入存入 `state.items`；`validItems()` 仅发送型号非空且尺寸、重量、数量均大于零的行，因此不完整行可能被前端静默排除。文件导入先保存在 `state.importPreview`，确认后 `appendSkus()` 追加有效行；AI 结果则经后端结构校验后直接追加，不走同一导入确认面板。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)

CSV/TXT/TSV 用标准库解析，尝试 UTF-8、GB18030、Big5，识别常见中英文列名；XLSX 直接用 ZIP/XML 读取共享字符串或 inline string，没有 openpyxl。当前选择按文件名排序的首个 `xl/worksheets/sheet*.xml`，不是按 workbook 关系解析的用户可见首张表；没有公式计算、合并单元格展开或自动 mm/m 换算。数字解析只取首个数字，模板明确要求人工将 mm 除以 10。文件压缩体积限制为 5 MB，未限制 XLSX 解压后总体积。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)

### 2. 自动初稿

`calculate()` → `/api/pack` → `_packing_spec()` → `smart_pack()` → PNG → `validate_plan()` → 前端替换 placements、清空撤销历史、取消层过滤及回放、重绘。自动排柜不保留已锁定布局，要保留锁定部分必须调用另一条重排路径。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)

- `_best_grid()` 枚举摆放方向，以“装入箱数最多，其次占用柜长最短”评分；直立货物只有水平两种朝向，可侧放货物最多六种去重方向。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py)
- compact 按 flat 优先、SKU 总体积降序，沿 X 推进；可用 flat 箱顶平台，并回填上组同尺寸末列空位。平台必须按实际单箱占地生成，不能把未铺满网格当成实体支撑面。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [tests/test_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_packer.py)
- grouped 是排序与放置优先级策略，不是严格空间隔离：flat 全局优先，其余按 arrival_order、厂家、体积排序，地板优先、平台兜底，禁用末列回填。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py)
- auto 仅当至少两个非空厂家、compact 利用率小于 75%、且 compact 全部装入时切 grouped；切换后没有与 compact 做结果优劣比较或失败回退。该判断在 `smart_pack()` 和 `api_pack()` 各有一份。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)
- 初稿算法执行总重限制，但不在生成阶段落实上压/分段限重；这些规则通过最终校验暴露，不能把初稿视作必然合法布局。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)

### 3. 两种局部重排不能混淆

**后端未锁定重排**：保留传入锁定箱原位，以清单数量减锁定数量生成剩余箱；方向枚举 + 候选边缘点，候选按 Z/X/Y 排序，找到可行位置即接受。检查总重、边界、碰撞、完整支撑、下方是否可承压和累计上压。分段限重仍只在最终校验检查；锁定箱本身即便悬空、超量或占用门口也不会被自动修正。候选地板笛卡尔积超过 8000 时使用较小候选集控制规模。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py)

**前端当前层重排**：`repackCurrentLayer()` → `repackLayerPlane()`，不调用后端重排接口；只移动当前层未锁定箱的 X/Y，保持尺寸与原锁定状态，其他箱作为固定障碍。按体积降序尝试位置，检查完整支撑、边界、门口及碰撞，但不检查累计上压/不可叠等完整规则，完成后再请求正式校验。有上层货物先弹确认。层归属以 Z 四舍五入到 5 cm 判断，重排会将该组箱的实际 Z 设为层值。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)

### 4. 规则校验

`validate_plan()` 是正式规则集中入口，输出 severity/code/message/item/instance_id，而非抛错阻止编辑。漏放为 warning，但安全摘要将未装箱数视为不可交付。[_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)

- 支撑要求底面 100% 被同一高度接触矩形的并集覆盖，容差 `EPS=1e-6`；支撑不能重复计面积。累计上压从高 Z 向低 Z 传递，按接触面积/上箱底面积分摊上箱自重及已承受重量。此模型不是结构力学分析。[_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py)
- 六段重量及前后/左右半柜重量都按单箱中心点归段，整箱重量计入一个区域，并非按箱体跨段面积分摊。前端、本接口统计、校验器各有相关实现。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py)
- 偏载告警只在总重超过额定载重 20% 时启用；默认 X/Y 重心偏离 50% 超过 12 个百分点才警告，不计算车辆真实轴荷。[_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py)
- 碰撞扫描每个外层箱发现首个冲突就停止内层搜索，并把问题挂到该箱上；结果不是完整碰撞对清单，也不保证双方都高亮。[_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)

## 前端编辑、持久化与导出

- 典型编辑事务是：`snapshot()` → 修改 placements → `manualTouched=true` → `pushHistory()` → `renderAll()` → `recordActivity()` → `validatePlan()`。撤销栈最多 80 个，仅保存 placements，不回滚清单、项目字段、标注、视图、人工复核标记或活动日志。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- 拖动默认 5 cm 网格并向可见箱体边缘/柜壁吸附；侧视拖动改 X/Z。前端即时提示只覆盖碰撞、门口占用，不能代替后端规则。快速修复只是移位/落地候选动作，可能产生其他问题，必须保持后续校验。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- `.cpack` 是 JSON，`projectPayload()` 输出 `version:9`。手动存档与自动草稿共用该函数，保存项目元数据、清单、placements、规则、层/回放/视图状态、正式标注、自定义视图及日志；不保存撤销栈、选择、内部剪贴板、校验结果或普通当前缩放缓存。`applyProjectData()` 用默认字段兼容旧数据，但没有按 version 严格校验/迁移。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- 浏览器草稿键为 `container-pack-autodraft-v1`，650 ms 防抖并在 beforeunload 保存；布局另存 `container-pack-layout-v1`，不属于项目文件。正式测量标注最多 40 条、视图预设最多 30 条、日志最多 200 条，面板显示最近 8 条，HTML 报告带最近 40 条。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- CSV 和 HTML 完全在浏览器生成；PNG、Excel 在后端生成。Excel 为自写 OOXML ZIP，共七张表：摘要、货物清单、装柜坐标、校验问题、分段重量、未放货物、操作记录；没有公式计算能力。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)
- HTML 报告先提示未完成流程，允许人工确认后继续；快照恢复所有层/装柜步骤，并临时清除选择与临时测距，但保留正式标注。PNG 渲染器不接收规则问题、门口区域或标注参数，不能把 HTML/SVG 的可视化能力推广到 PNG。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [_visualizer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_visualizer.py)

## 需保留的约束与已定位风险

### 业务/实现约束

1. 保留“算法给初稿，统一校验给问题，人工仍能编辑及确认导出”的边界；规则更改同时检查初稿、后端重排、前端层内重排三条路径，不能只改一个求解函数。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
2. 身份、数量、单位、`flat/full/none` 与侧放映射必须贯通请求模型、数据类、项目文件、导入和导出。复制摆放需要新实例号并受清单剩余数量约束；锁定重排保留原锁定箱坐标和颜色。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py)
3. `DASHSCOPE_API_KEY` 仅从环境读取，无默认密钥；未设置时提取返回 503，其他功能继续使用。`QWEN_VL_MODEL` 默认 `qwen3.6-plus`，HTTP 调用当前强制绕过代理，超时 180 秒。这是当前实现选择，不是所有部署环境必须遵循的通用网络规则。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)
4. 文本维护遵守 UTF-8、CRLF、末尾换行；Markdown 不裁剪尾随空格。乱码门禁按已知模式检测，不是完整语言质量验证。[.editorconfig](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/.editorconfig) [text_quality.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/text_quality.py)

### 不应被文档完成声明掩盖的问题

- **校验与安全状态可能不同步**：`validatePlan()` 采用 180 ms 定时请求，没有请求序号/取消机制；响应仅刷新问题与画布，不刷新统计安全卡/流程面板。清单字段编辑也不会统一触发校验。`exportReport()` 不等待新校验，直接使用缓存 validation；因此 README 的“实时校验”不能理解为任意状态下都已同步验证。修复入口是 `validatePlan()`、输入提交及 `exportReport()`。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [README.md](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/README.md)
- **锁定不是全局只读**：拖动、旋转、微调、快速修复会跳过锁定箱，但单箱数字字段和删除动作没有相同保护。撤销也仅恢复 placements。修改锁定语义时要逐入口核对，不能依赖按钮名称。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- **重复 SKU 不具备一致语义**：导入仅警告后继续追加；校验器的 SKU/需求字典按 model 覆盖，而排柜逐行生成且实例号从每行重新计数，可能导致数量、身份和高亮关联异常。优先核对 `_parse_manifest_rows()`、`_to_skus()`、`_pack_compact()`、`validate_plan()` 与前端数量统计。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- **手工 placement 与 SKU 的一致性检查有限**：校验器只对 upright_only SKU 校验尺寸朝向，不验证可侧放箱的尺寸是否为原尺寸排列，也不核验 placement 重量等于 SKU 单重、实例号是否重复；API 的数值范围限制不能代替这些语义检查。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py)
- **堆叠约束并未覆盖所有路径**：末列回填仅比较尺寸和总重，不复核当前 SKU 的堆叠模式；统一校验器检查下箱能否承压，但没有单独禁止 flat 箱被人工放到上层。后端候选重排对此反而更严格。相关修改应保留平台不悬空回归，并增加对应语义用例。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [tests/test_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_packer.py)
- **“完整报告”仍可能被当前视窗裁切**：`planSVGForLimit()` 取消层过滤/回放限制，却不重置当前 viewBox 或高亮；门口聚焦、缩放及厂家淡化状态会进入报告。数据行完整不代表整柜图完整可见。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [README.md](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/README.md)
- **草稿并非跨所有启动端口共享**：localStorage 按浏览器 origin 隔离，而启动端口会自动变化；换端口可能看不到原草稿。清草稿只删除存储、不清页面，后续编辑/重绘或退出保存可能重新写入；目前也未清除待执行 draftTimer。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py)
- **渲染降级是有限的**：`/api/pack` 只捕获渲染产生的 HTTPException，允许空 PNG 并返回 render_error；其他绘图异常仍可能使接口失败。`/api/render_plan` 无同样降级，前端自动排柜也未显示 render_error。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py)
- **导入/识别边界仍需注意**：文本识别请求只有最小长度，无最大长度；图片 10 MB 和清单 5 MB 均在读入完整内容后检查；AI 提取的算术推断来自提示词，没有本地独立算术一致性校验。不能把提示词要求当成本地校验能力。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py)

## 按开发任务定位

| 任务 | 优先阅读与修改位置 | 已有回归入口 |
|---|---|---|
| 排柜质量、平台、方向、厂家策略 | `_best_grid()`、`smart_pack()`、`_pack_compact()`，以及 API 重复 auto 判断。[_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) | `tests/test_packer.py` 的示例与平台悬空回归；API 门口预留契约。[tests/test_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_packer.py) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) |
| 新规则或承重修正 | `validate_plan()`、`_can_place_candidate()`、`canPlaceLayerCandidate()`；同步 rulesPayload、模型、统计、安全摘要、报告。[_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) | `tests/test_validator.py`、`tests/test_app_contract.py`。[tests/test_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_validator.py) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) |
| 导入字段/单位/多表支持 | `_IMPORT_HEADER_ALIASES`、`_read_import_xlsx_rows()`、`_parse_manifest_rows()`、模板、`appendSkus()` 和预览。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) | CSV 中文表头、XLSX、空模板、无效行测试。[tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) |
| 编辑交互、布局、持久化 | `state`、编辑事务函数、`projectPayload()`/`applyProjectData()`、草稿与布局初始化。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) | 页面契约测试，再执行真实浏览器烟测；字符串断言不证明操作结果。[tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) [browser_smoke.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/browser_smoke.py) |
| 报告/Excel/PNG | 浏览器 `exportReport()`/`planSVGForLimit()`；后端 `_workbook_rows()`/`_build_xlsx()`；PNG `render_loading_plan()`。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_visualizer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_visualizer.py) | 工作簿契约与严格渲染 preflight；现有资料未见 HTML 报告截图回归。[tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) [preflight.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/preflight.py) |
| AI 接入、部署/打包 | `_post_dashscope()`、提取路由、请求限制；`main()`、`build.bat` 的真实打包参数。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [build.bat](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/build.bat) | 提取结果规范化测试、全套 preflight；不等于真实远端模型或 exe 启动验证。[tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) [preflight.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/preflight.py) |

算法任务表中的源码定位为 [_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py)；修改时同时检查 [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) 中的调度逻辑。

## 运行、测试与验收入口

以下是已有入口，不代表已在当前环境执行通过。建议使用 Python 3.11–3.13，打包脚本会强制检查该范围；运行依赖为 FastAPI、Uvicorn、Pydantic 2、python-multipart、Matplotlib，开发依赖额外加入 Playwright。[requirements.txt](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/requirements.txt) [requirements-dev.txt](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/requirements-dev.txt) [build.bat](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/build.bat)

```text
python -m pip install -r requirements.txt
python app.py

python -m unittest discover -s tests
python text_quality.py
python preflight.py
python preflight.py --strict-render

python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python browser_smoke.py
python preflight.py --strict-render --browser-smoke
```

上述命令分别由启动主函数、unittest discovery、自检与浏览器脚本提供。Windows 打包使用 `.\build.bat`，输出 `dist\ContainerPack.exe`；脚本执行严格渲染 preflight，但不自动执行浏览器烟测。[app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [preflight.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/preflight.py) [browser_smoke.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/browser_smoke.py) [build.bat](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/build.bat)

- 算法/规则改动可先执行 `python -m unittest discover -s tests -p test_packer.py` 和 `python -m unittest discover -s tests -p test_validator.py`；API/导入/导出改动执行 `python -m unittest discover -s tests -p test_app_contract.py`。[tests/test_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_packer.py) [tests/test_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_validator.py) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py)
- preflight 顺序是 Python 编译 → 文本质量 → unittest → API smoke，可选最后执行浏览器烟测。API smoke 覆盖首页、CSV 导入、排柜/校验、模板及工作簿 ZIP；strict-render 要求排柜返回 PNG，但不验证图片内容，也没有单独调用 `/api/render_plan`。[preflight.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/preflight.py)
- 真实浏览器烟测新建 1440×900 Chromium 上下文，验证首页标题/乱码、示例排柜、SVG/统计、草稿写入、三个分隔条拖动、布局存储及重置。未测试货物拖动、锁定、层内重排、报告导出或刷新后草稿恢复；右侧分隔条和面板拖柄只检查存在。[browser_smoke.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/browser_smoke.py)
- `tests/test_browser_smoke_contract.py` 只检查脚本文本包含关键入口；许多前端契约也只是首页字符串断言。`tests/test_preflight.py` 的测试名称含 passes，不是执行成功记录。[tests/test_browser_smoke_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_browser_smoke_contract.py) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) [tests/test_preflight.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_preflight.py)
- **依赖缺口**：测试与 preflight 使用 FastAPI TestClient，但两份 requirements 都未显式声明其所需的 `httpx`；干净环境的可执行性需先核对，不能凭安装 README 推定测试环境完备。[requirements.txt](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/requirements.txt) [requirements-dev.txt](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/requirements-dev.txt) [tests/test_app_contract.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/tests/test_app_contract.py) [preflight.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/preflight.py)
- `text_quality.py` 的跳过目录只有 `.git`、build、dist、`__pycache__`，并不跳过仓库内 `.venv`/venv，可能扫描第三方环境文件；这与 `.gitignore` 是否忽略虚拟环境无关。[text_quality.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/text_quality.py) [.gitignore](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/.gitignore)

## 文档与静态事实的取舍

README/CHANGELOG/PRODUCT_PLAN 可用于理解需求来源，但“已完成”“已有 41 个测试”等陈述不能代替当前测试发现与运行结果。PRODUCT_PLAN 一方面记载已加入浏览器烟测，近期优先列表仍写“浏览器烟测脚本化”，属于规划文本未完全同步；以现有 `browser_smoke.py` 的实际覆盖为准。[README.md](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/README.md) [CHANGELOG.md](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/CHANGELOG.md) [PRODUCT_PLAN.md](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/PRODUCT_PLAN.md) [browser_smoke.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/browser_smoke.py)

下一轮修改前的具体阅读顺序：安全与报告问题先读前端 `validatePlan()` → `workflowSteps()`/`safetySummary()` → `exportReport()`，再对照后端 `_safety_summary_for_export()`；排柜/规则问题先读 `_pack_compact()` → `validate_plan()` → `_can_place_candidate()` → `repackLayerPlane()`。这些路径存在重复逻辑和不同约束，是本批源码中最需要同步维护的位置。[_frontend.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_frontend.py) [app.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/app.py) [_packer.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_packer.py) [_validator.py](https://github.com/Winkless213/container-loading-planner/blob/ee4bd9325b440246b78b0cc604a253e66ade7da7/_validator.py)
