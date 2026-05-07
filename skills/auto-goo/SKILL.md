---
name: auto-goo
description: This skill should be used when the user says "开始任务", "/auto-goo", "run:", or gives any multi-step task that can be decomposed into sub-tasks. Automates the full workflow: parse task into DAG → parallel/serial execution via Subagent dispatch → optimization iteration → Goo-wiki archiving. Requires Read, Write, Edit, Bash, WebSearch, Agent tools.
tools: Read, Write, Edit, Bash, WebSearch, Agent
---

# AutoGoo 自动化工作流

AutoGoo 是一个任务编排框架。收到可分解的任务后，按以下四个阶段执行。

## Phase 1: 任务解析

**收到任务后必须先解析为 DAG，不得跳过规划直接动手编码。**

解析步骤：
1. 识别最终交付物 — 问"用户最终要拿到什么？"
2. 逆向拆解 — 从目标倒推，追问到"不可再分"的原子步骤
3. 标注依赖关系 — 识别前置条件，推导拓扑顺序
4. 识别优化标记 — 含性能关键词 → 标记 `type: "optimize"`
5. 输出 `.goo/plan.json`

同一轮次的步骤（无依赖或依赖已完成）必须并行分发。

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

每个步骤启动一个 Subagent。Subagent 的 prompt 必须包含完整上下文（任务描述 + 上游输出 + 交付要求）。

Subagent prompt 模板（exec / optimize / eval 三种变体）、错误处理策略、上下文传递规则 → `references/execution-engine.md`

**日志铁律：每一步执行必须归档。** 每步写一份 `.goo/logs/{timestamp}_step-{id}_{name}.md`。失败也要写日志记录原因。

## Phase 3: 优化迭代

当步骤标记为 `type: "optimize"` 时启动优化循环：

1. WebSearch 搜索该领域标准评价指标
2. 实现基线版本并评测
3. 瓶颈分析（profile / 大 O / 磁盘吞吐，至少一种）
4. 优化 → 同指标评测对比
5. 按终止条件决定是否继续（< 20% 提升则停止）

指标模板、评测规范、终止条件表 → `references/optimization-loop.md`

## Phase 4: Obsidian 归档

每步完成后启动 Recorder Subagent，将执行记录转为 Goo-wiki 格式的 Obsidian 笔记。

- 归档路径：`Goo-wiki/wiki/projects/<project-slug>/` 或 fallback `.goo/obsidian/`
- YAML frontmatter 规范、wikilink 格式、log.md 追加格式 → `references/obsidian-archive.md`

Goo-wiki vault 检测：默认检查 `~/workspace/Goo-wiki/CLAUDE.md`。路径可配置，见 `references/setup.md`。

## Python 项目规范

当任务涉及 Python 实现时：
- Python 3.10+，完整类型注解，ruff lint（line-length=100）
- 优先使用标准库，外部依赖在 plan.json 声明
- 不 scope creep — 不做任务描述未要求的功能

完整规范 → `references/python-standards.md`

## 快捷命令

| 用户说 | 行为 |
|--------|------|
| "开始任务 / run: / 做这个" | Phase 1 → Phase 2 |
| "优化 / optimize" | 启动 Phase 3 |
| "评测 / evaluate / benchmark" | 搜索指标 → 评测 → 记录 |
| "状态 / status / 进展" | 展示 `.goo/logs/_summary.md` |
| "日志 / logs" | 列出 `.goo/logs/` 下所有文件 |
| "重新规划 / replan" | 重新解析任务 |
| "继续 / continue" | 从上次中断处继续 |
| "并行执行 / parallel" | 分发当前轮全部无依赖步骤 |
| "重试 / retry" | 重试失败的步骤 |

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
