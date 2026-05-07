---
name: auto-goo
description: "This skill should be used when the user says '开始任务', '/auto-goo', 'run:', or gives any multi-step task that can be decomposed into sub-tasks. Automates the full workflow: parse task into DAG, parallel/serial execution via Subagent dispatch, optimization iteration, Goo-wiki archiving. Requires Read, Write, Edit, Bash, WebSearch, Agent tools. Should NOT trigger for single-step tasks, pure Q&A, or tasks already covered by a more specific skill."
version: 0.1.0
tools: [Read, Write, Edit, Bash, WebSearch, Agent]
---

# AutoGoo 自动化工作流

收到可分解的多步任务后，按以下四个阶段执行。单步任务或纯问答不需启动此流程，直接执行即可。

## Phase 1: 任务解析

**必须先解析为 DAG，不得跳过规划直接动手编码。**

解析步骤：
1. 识别最终交付物 — "用户最终要拿到什么？是脚本、模型、报告还是系统？"
2. 逆向拆解 — 从目标倒推，追问到"不可再分"的原子步骤。如果任务本身就是单步的（如"把这个文件转成 PDF"），直接执行，不走此流程。
3. 标注依赖关系 — 识别前置条件，推导拓扑顺序。原始数据准备 → 处理 → 输出，每一步依赖前一步的输出。
4. 识别优化标记 — 含"性能、速度、延迟、吞吐、效率、内存、GPU、耗时"关键词 → 标记 `type: "optimize"`
5. 输出 `.goo/plan.json`

### 步骤粒度原则

- 每步应产出可验证的中间结果（文件、指标、报告）
- 步骤过多（>10）说明拆分过细，考虑合并
- 步骤过少（<2）说明拆分不够，需要继续追问"还需要什么"

### plan.json 概要

```json
{
  "task": "<任务描述>",
  "created_at": "YYYY-MM-DDTHH-MM-SS",
  "steps": [
    {
      "id": 1,
      "tier": 1,
      "name": "<步骤名>",
      "description": "<做什么>",
      "depends_on": [],
      "type": "exec"
    }
  ]
}
```

完整 schema、时间戳格式、依赖声明规则 → `references/task-parsing.md`

## Phase 2: 执行

按 DAG 拓扑轮次逐轮执行。每轮内**所有无依赖步骤必须并行分发**。

```
for each 执行轮:
  该轮步骤 → 同时派发多个 Agent (run_in_background)
  等待全部 Agent 完成
  收集结果 → 写入 .goo/logs/
  检查失败 → 重试或标记
```

### Subagent 分发

每个步骤启动一个 Subagent。Prompt 构造原则：
- 任务描述（step.name + step.description）必须完整
- 上游输出摘要必须包含（文件路径 + 关键数据）
- 交付要求必须明确（写日志、输出位置）

### 失败处理

| 场景 | 处理 |
|------|------|
| 单个 Agent 失败 | 记录错误日志，重试 1 次 |
| 重试仍失败 | 标记 ❌ failed，继续不依赖它的步骤 |
| 关键路径失败 | 通知用户，询问是否继续 |
| Agent 超时（>5 分钟） | 视为失败，按失败流程处理 |

### 日志铁律

每一步执行必须归档。失败也要写日志记录原因。日志时间戳统一使用 `YYYY-MM-DDTHH-MM-SS`。

Subagent prompt 模板（exec / optimize / eval 三种变体）、上下文传递规则 → `references/execution-engine.md`

## Phase 3: 优化迭代

当步骤标记为 `type: "optimize"` 时启动。

**快速跳过条件**（满足任一则跳过）：
- 基线指标已达标（用户认可当前性能）
- 客观无提升空间（IO 瓶颈已达硬件上限）
- 用户明确说"不需要优化"

### 完整循环

1. WebSearch 搜索该领域标准评价指标
2. 实现基线版本并评测（至少 3 次取平均）
3. 瓶颈分析 — cProfile / py-spy / tracemalloc / 大 O 推算，至少一种
4. 优化 → 同指标评测对比
5. 终止判断：提升 < 20% 或连续两轮 < 5% 停止

### 评测约束

- 计时与内存测量分开进行（tracemalloc 拖慢计时）
- 测量前 warmup 至少 3-5 次
- 优先使用 pyperf 减少系统噪声

指标模板、终止条件表、领域推荐指标 → `references/optimization-loop.md`

## Phase 4: Obsidian 归档

每步完成后启动 Recorder Subagent，将执行记录转为 Goo-wiki 格式的 Obsidian 笔记。

- 归档路径：`Goo-wiki/wiki/projects/<project-slug>/` 或 fallback `.goo/obsidian/`
- 如果 Goo-wiki vault 不存在且 `.goo/obsidian/` 也不必要（临时项目），跳过归档，仅保留 `.goo/logs/` 日志
- YAML frontmatter 规范、wikilink 格式、log.md 追加格式 → `references/obsidian-archive.md`

Goo-wiki vault 检测：默认检查 `~/workspace/Goo-wiki/CLAUDE.md`。路径可配置，见 `references/setup.md`。

## Python 项目规范

当任务涉及 Python 实现时：
- Python 3.10+，完整类型注解，ruff lint（line-length=100）
- 优先使用标准库，外部依赖在 plan.json 声明 `[dep: <包名>]`
- 不 scope creep — 不做任务描述未要求的功能

完整规范 → `references/python-standards.md`
## 附加资源

### Reference Files
- **`references/setup.md`** — 环境设置、Goo-wiki 路径配置、推荐 SessionStart hooks
- **`references/task-parsing.md`** — plan.json schema、解析流程、依赖与并行判断规则
- **`references/execution-engine.md`** — 执行流程、Subagent prompt 模板、错误处理、日志格式、上下文传递
- **`references/optimization-loop.md`** — 完整循环、指标模板、评测规范、终止条件
- **`references/obsidian-archive.md`** — Goo-wiki 归档规范、Recorder prompt、笔记类型与命名
- **`references/python-standards.md`** — 代码风格、项目结构、核心接口约定

### Examples
- **`examples/csv-analysis-workflow.md`** — 完整工作流示例（CSV 销售数据分析）

### Scripts
- **`scripts/init-plan.sh`** — 初始化 plan.json 模板

### Agents
- **`../../agents/obsidian-recorder.md`** — Obsidian 归档 Subagent
