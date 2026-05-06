# AutoGoo — 自动化智能体编排框架

## 项目定位

AutoGoo 是一个自动化智能体编排框架。接收用户任务后自动解析为执行步骤，按依赖关系并行或串行执行，遇到性能优化场景自动迭代，并自动搜索评价指标用于评测。每一步执行都必须留下结构化记录。

**核心原则**：
- **先解析，再执行** — 绝不直接动手，先规划成 DAG
- **能并行就不串行** — 无依赖的步骤必须并行分发
- **优化必有指标** — 没有量化指标就不算优化
- **执行必留痕** — 每一步都归档到 `.goo/logs/`

## 快速开始 (Quick Start)

每次会话加载后，按以下顺序行动：

```
1. 检查 Goo-wiki 路径是否存在
   → ls /home/zixigu/workspace/Goo-wiki/CLAUDE.md
   （不存在则仅使用 .goo/ 本地记录，跳过 Obsidian 归档）

2. 检查是否有上次未完成的任务
   → 读取 .goo/plan.json（如果存在）
   → 如果 plan.json 中有未完成的步骤 → 询问用户是否继续

3. 等待用户下达任务
```

## 核心工作流

```
用户任务 → [任务解析] → plan.json(DAG) → [执行引擎] → 记录归档
                                    ↓ (若含优化标记)
                           [优化迭代循环] → [指标搜索] → 评测 → 对比记录
```

---

## 1. 任务解析 (Task Parsing)

收到用户任务后，**第一步必须是任务解析**，不得跳过规划直接编码。

### 1.1 解析流程

```
Step 1: 识别最终交付物
  → 问自己："用户最终要拿到什么？是一个脚本、一个模型、一份报告还是一套系统？"

Step 2: 逆向拆解
  → 从最终目标倒推："要交付这个，需要先有什么？"
  → 持续追问直到拆成"不可再分"的原子步骤

Step 3: 标注依赖关系
  → 步骤 A 必须在 B 之前完成 → A depends_on B
  → 步骤 A 和 B 互不依赖 → 标记为可并行 (parallel: true)
  → 步骤 A 和 B 都依赖 C → C 完成后 A 和 B 并行

Step 4: 识别优化标记
  → 如果任务描述包含：性能、速度、延迟、吞吐、效率、内存、GPU、耗时 → type: "optimize"
  → 如果涉及模型训练/推理 → 自动标记 optimize + 后续自动搜索评测指标

Step 5: 输出 plan.json
```

### 1.2 解析 Prompt 模板

每次收到任务后，按以下模板在脑中执行（不需要输出给用户看，除非用户要求）：

```
## 任务分析

最终交付物：<一句话描述>

倒推步骤链：
1. <步骤名> — <做什么>
   - 依赖：<前置步骤>
   - 可并行：<true/false>
   - 类型：<exec/optimize>
   ...

DAG 结构总结：
- 串行链：<哪些必须逐个做>
- 并行组：<哪些可以同时做>
- 优化任务：<是否含性能优化>
```

### 1.3 plan.json 格式

```json
{
  "task": "用 Python 实现一个高性能 CSV 解析器",
  "created_at": "2026-05-06T14:30:00+08:00",
  "steps": [
    {
      "id": 1,
      "name": "调研现有 CSV 解析方案",
      "description": "搜索 Python csv / pandas / polars 对比，确定基准",
      "depends_on": [],
      "parallel_group": "A",
      "type": "exec",
      "estimated_time": "5min"
    },
    {
      "id": 2,
      "name": "实现基线 CSV 解析器",
      "description": "用 Python csv 模块实现一个基准版本",
      "depends_on": [1],
      "parallel_group": null,
      "type": "exec"
    },
    {
      "id": 3,
      "name": "实现优化版 CSV 解析器",
      "description": "用 memory-mapped IO + 向量化解析优化",
      "depends_on": [1],
      "parallel_group": null,
      "type": "optimize"
    },
    {
      "id": 4,
      "name": "评测与对比",
      "description": "搜索 CSV benchmark 标准指标，评测两个版本并对比",
      "depends_on": [2, 3],
      "parallel_group": null,
      "type": "eval"
    }
  ],
  "parallel_groups": {
    "A": [1]
  }
}
```

### 1.4 依赖与并行判断规则

| 情况 | 策略 |
|------|------|
| `depends_on` 为空且互不引用 | 并行分发 |
| `depends_on` 相同 | 前驱完成后并行 |
| `depends_on` 有传递链 | 按拓扑序串行 |
| 一个步骤的输出是另一个的输入 | 串行 (即使忘记标注也要推断) |

**执行顺序提取算法**（脑内执行）：
```
1. 找出所有 depends_on 为空的步骤 → 第一轮执行
2. 移除第一轮步骤，找出新的 depends_on 为空的 → 第二轮
3. 重复直到所有步骤执行完毕
4. 同一轮内的步骤 → 并行；跨轮 → 串行
```

---

## 2. 执行引擎 (Execution Engine)

### 2.1 执行流程

```
for each 执行轮:
  该轮内所有步骤 → 并行分发
  for each 并行步骤:
    启动 Agent 执行 (run_in_background)
  等待所有 Agent 完成
  收集结果 → 写入日志
  检查是否有失败 → 重试或终止
进入下一轮
```

### 2.2 Agent 分发模板

并行分发时，Agent prompt 必须包含以下上下文：

```
## 任务
<步骤的 name + description>

## 上下文
<前驱步骤的输出摘要>

## 要求
1. 执行完成后将结果写入 .goo/logs/ 目录
2. 记录关键决策和耗时
3. 如果遇到问题，记录错误详情而不是悄无声息地失败
```

### 2.3 错误处理

| 情况 | 处理方式 |
|------|---------|
| Agent 执行失败 | 记录错误日志，重试 1 次 |
| 重试仍失败 | 标记为 ❌ failed，继续执行不依赖它的步骤 |
| 关键路径失败 | 通知用户，询问是否继续 |
| 部分成功 | 合并已成功的结果，标注失败步骤 |

### 2.4 结果合并

所有并行 Agent 完成后：
1. 收集每个 Agent 写入的 `.goo/logs/` 记录
2. 汇总到 `.goo/logs/_summary.md`
3. 通知用户完成状态

---

## 2.5 Subagent 任务分配 (Subagent Dispatch)

每个步骤的执行通过 Subagent 完成。关键原则：**给 Subagent 的 prompt 必须包含完整的上下文，但不替它做决策。**

### 2.5.1 通用 Dispatch 流程

```
plan.json 中的每一步
  → 构造 Subagent Prompt（含：任务描述、上游输出、交付要求）
  → 并行步骤 → 同时派发多个 Agent (run_in_background)
  → 串行步骤 → 等待上一个完成后派发
  → 每个 Subagent 完成后写入 .goo/logs/
  → 收集结果，传递给下游步骤
```

### 2.5.2 Subagent Prompt 构造模板

根据步骤类型，使用不同的 prompt 模板：

**执行型 (type: "exec")**：
```
你是一个 AutoGoo 执行 Subagent。

## 任务
{step.name}: {step.description}

## 上游上下文
{upstream_outputs}  ← 前驱步骤的输出摘要

## 交付要求
1. 在 {cwd} 目录下工作
2. 完成后将结果写入 .goo/logs/{timestamp}_step-{id}_{name}.md
3. 日志必须包含：做了什么、关键决策、输出产物路径、耗时
4. 如果失败，记录错误详情并返回失败标志

## 产物
- 代码文件写入 src/ 或对应目录
- 评测数据写入 .goo/
```

**优化型 (type: "optimize")** — 在 exec 模板基础上追加：
```
## 优化要求
- 先测量基线性能，再优化
- 每次优化后必须用相同指标评测
- 记录优化前后对比
- 如果连续两次无提升，停止并报告
```

**评测型 (type: "eval")**：
```
你是一个 AutoGoo 评测 Subagent。

## 评测任务
{step.description}

## 待评测产物
{upstream_outputs}  ← 上游步骤产出的文件路径/数据

## 要求
1. 先搜索该领域标准评价指标 (WebSearch / context7)
2. 定义明确的评测 protocol（硬件、数据集、运行次数）
3. 执行评测
4. 写入 .goo/logs/ 和 .goo/eval-metrics.md
```

### 2.5.3 Agent 编排示例代码 (脑内执行)

当需要跨文件/跨模块并行时，遵循以下模式：

```python
# 脑内编排模式（非实际代码，是执行策略）

# 并行组
parallel_group = [step_2, step_3]  # 互不依赖

# 对每个步骤派发 Agent
for step in parallel_group:
    agent_prompt = build_prompt(step, upstream_context)
    dispatch_agent(step.id, agent_prompt, run_in_background=True)

# 等待所有完成
results = await wait_all()

# 传递给下一轮
next_round_input = merge_results(results)
```

### 2.5.4 Subagent 间上下文传递规则

| 上游产出类型 | 传递方式 | 示例 |
|-------------|---------|------|
| 代码文件 | 传递文件路径 | `/src/parser/baseline.py` |
| 数据文件 | 传递路径 + schema | `/data/benchmark_results.json` |
| 分析结论 | 直接写在 prompt 中 | "基线吞吐为 125k rows/s" |
| 模型权重 | 传递路径 + 指标 | `/models/checkpoint.pt, acc=0.92` |

### 2.5.5 并行分发检查清单

分发并行 Agent 前，确认以下条件：

- [ ] 步骤间真的没有数据依赖？→ 检查前驱输出是否被对方需要
- [ ] 步骤间不会写同一个文件？→ 如果有共享资源，加锁或分目录
- [ ] 每个 Agent 的 prompt 包含足够上下文？→ 至少包含任务描述 + 前驱输出
- [ ] 每个 Agent 知道往哪里写日志？→ .goo/logs/ 路径
- [ ] 有超时机制？→ 单个 Agent 默认超时 5 分钟

### 2.5.6 Subagent 分类速查

| 类型 | 用途 | 典型工具 | 返回格式 |
|------|------|---------|---------|
| **Research** | 调研、搜索、收集信息 | WebSearch, context7, Read | `.md` 报告 |
| **Implementer** | 写代码、实现功能 | Write, Edit, Bash | 文件路径 |
| **Optimizer** | 性能分析和优化 | Bash(profiling), Edit | 对比报告 |
| **Evaluator** | 评测、benchmark | Bash, WebSearch | 数值指标 |
| **Reviewer** | 审查代码或方案 | Read, Grep | Review 报告 |
| **Recorder** | Obsidian 知识归档 | Write | 格式化 `.md` |

### 2.5.7 Obsidian Recorder — 知识归档 Subagent

每次任务执行后，Recorder 负责将执行过程转化为符合 Goo-wiki 规范的 Obsidian 笔记，实现执行记录自动沉淀为可追溯、可检索的知识库。

**不设独立 `auto-goo/` 目录**，而是按任务所属领域放入对应目录，通过 `auto-goo` tag 区分来源。

**遵守 Goo-wiki 约定**：
- 按项目放入 `wiki/projects/<project-slug>/` 下
- 指标类知识放入 `wiki/concepts/<domain>/`
- YAML frontmatter 使用 Goo-wiki 标准格式（type, title, status, tags, aliases, date）
- 所有笔记追加 `tags: [auto-goo]` 标记来源
- 文件名使用小写连字符（`lowercase-with-hyphens.md`）
- 默认使用中文
- 每次任务完成后向 `Goo-wiki/log.md` 追加活动日志
- 不写入 `raw/` 目录（原始来源不可变）
- 成熟度 status: `seed`（初始记录） → `developing`（补充后） → `stable`（已验证）
- 使用 `[[Wikilink]]` 建立双向链接

**输出目录**：
1. **优先** → `Goo-wiki/wiki/projects/<project-slug>/`（Goo-wiki vault 存在时）
2. **fallback** → `.goo/obsidian/<project-slug>/`（Goo-wiki 不存在时，仅本地归档）

Goo-wiki 路径检测：检查 `/home/zixigu/workspace/Goo-wiki/CLAUDE.md` 是否存在。不存在则降级为 fallback 模式。

**触发时机**：每步完成后触发归档 + 全部完成后生成汇总笔记

**笔记类型**：

| 笔记类型 | 路径（按项目领域） | Tag | 频率 |
|---------|-------------------|-----|------|
| 任务总览 | `wiki/projects/<project-slug>/<task-name>.md` | `[auto-goo, <domain>]` | 每次任务 |
| 步骤笔记 | `wiki/projects/<project-slug>/<task-name>-step-<id>.md` | `[auto-goo, <domain>, step]` | 每步一次 |
| 迭代记录 | `wiki/projects/<project-slug>/<task-name>-round-<n>.md` | `[auto-goo, <domain>, optimization]` | 每轮优化 |
| 指标档案 | `wiki/concepts/<domain>/<task-name>-metrics.md` | `[auto-goo, metrics]` | 追加累积 |
| 活动日志 | `log.md` | `## [YYYY-MM-DD] auto-goo | <task>` | 每次任务 |

#### 步骤笔记模板

```markdown
---
type: concept
title: "<task_name> - Step <id>: <step_name>"
domain: <project-slug>
status: seed
tags: [auto-goo, <project-slug>, step]
date: {{date}}
aliases:
  - "auto-goo-step-{{id}}"
---

# {{step_name}}

**任务**: [[wiki/projects/<project-slug>/<task-name>|<task_name>]]  
**状态**: {{status}} | **耗时**: {{duration}} | **来源**: `auto-goo`

## 关键决策

- {{decision_1}}
- {{decision_2}}

## 输出产物

- [[{{output_path}}|{{output_name}}]]
- [[{{output_path}}|{{output_name}}]]

## 备注

{{notes}}
```

#### 任务总览笔记模板

```markdown
---
type: project
title: "<task_name>"
domain: <project-slug>
status: developing
tags: [auto-goo, <project-slug>]
date: {{date}}
aliases:
  - "auto-goo-<project-slug>-<task-slug>"
---

# {{task_name}}

**来源**: `auto-goo`

## 步骤执行

| # | 步骤 | 状态 | 耗时 |
|---|------|------|------|
| 1 | [[wiki/projects/<project-slug>/<step-1-file>|<step_1_name>]] | ✅ | 4m |
| 2 | [[wiki/projects/<project-slug>/<step-2-file>|<step_2_name>]] | ✅ | 3m |

## 优化迭代

| 轮次 | 基线 | 优化后 | 提升 | 详情 |
|------|------|--------|------|------|
| 1 | 125k rows/s | 402k rows/s | +221% | [[wiki/projects/<project-slug>/<round-1-file>|详情]] |

## 指标汇总

| 指标 | Baseline | Optimized | 提升 |
|------|----------|-----------|------|
| 吞吐量 | 125k rows/s | 402k rows/s | +221% |
| 内存 | 45 MB | 52 MB | +15% |
```

#### 指标档案模板

```markdown
---
type: concept
title: "<task_name> 指标"
domain: <project-slug>
status: developing
tags: [auto-goo, metrics]
aliases:
  - "auto-goo-metrics-<task-slug>"
---

# {{task_name}} 指标

> AutoGoo 自动评测记录。任务详情见 [[wiki/projects/<project-slug>/<task-name>|<task_name>]]

| 指标 | Baseline | Optimized | 提升 |
|------|----------|-----------|------|
| 吞吐量 | 125k rows/s | 402k rows/s | +221% |
| 内存 | 45 MB | 52 MB | +15% |

---

*指标定义参考：<搜索来源>*
```

#### log.md 追加格式

每次任务完成后，向 `Goo-wiki/log.md` 追加一条记录：

```markdown
## [{{YYYY-MM-DD}}] auto-goo | {{task_name}}

执行 {{step_count}} 步，耗时 {{total_duration}}。含优化迭代 {{round_count}} 轮。
项目页：[[wiki/projects/<project-slug>/<task-name>|<task_name>]]`
```

#### Recorder Prompt 模板

当步骤完成或任务结束时，按以下模式派发 Recorder：

```
你是一个 AutoGoo Obsidian Recorder Subagent。

## 任务
将以下执行记录格式化为符合 Goo-wiki 规范的 Obsidian 笔记。

## 输入数据
{step_log_content}

## Goo-wiki 规范（必须遵守）
1. 不设独立 auto-goo 目录，按项目领域放入对应路径：
   - 任务/步骤/迭代 → wiki/projects/<project-slug>/
   - 指标 → wiki/concepts/<domain>/
2. 所有笔记 tags 必须包含 auto-goo
3. YAML frontmatter 格式：type, title, domain, status, tags, date, aliases
4. type 取值：concept（步骤/指标）、project（任务总览）
5. status 取值：seed / developing / stable
6. 文件名使用小写连字符
7. 默认使用中文
8. 用 [[wiki/projects/<project-slug>/xxx|显示名]] 格式的 wikilink
9. 数字和指标用表格呈现
10. 任务完成后向 Goo-wiki/log.md 追加一条活动日志
11. 不要写入 raw/ 目录
12. 输出目录优先级：Goo-wiki/wiki/ > .goo/obsidian/（fallback）
```

#### Goo-wiki vault 路径约定

按项目领域写入，不设独立 auto-goo 目录（Goo-wiki 不存在时 fallback 到 `.goo/obsidian/`）：

| AutoGoo 事件 | Goo-wiki 目标路径 | Fallback 路径 |
|-------------|------------------|--------------|
| 步骤完成 | `Goo-wiki/wiki/projects/<slug>/<task>-step-<id>.md` | `.goo/obsidian/<slug>/<task>-step-<id>.md` |
| 任务完成 | `Goo-wiki/wiki/projects/<slug>/<task>.md` | `.goo/obsidian/<slug>/<task>.md` |
| 迭代记录 | `Goo-wiki/wiki/projects/<slug>/<task>-round-<n>.md` | `.goo/obsidian/<slug>/<task>-round-<n>.md` |
| 指标累积 | `Goo-wiki/wiki/concepts/<domain>/<task>-metrics.md` | `.goo/obsidian/<slug>/<task>-metrics.md` |
| 活动日志 | `Goo-wiki/log.md`（追加一行） | 跳过（fallback 模式不写 log.md） |

## 3. 优化迭代循环 (Optimization Iteration)

当步骤标记为 `type: "optimize"` 时启动。

### 3.1 完整循环

```
┌─ Round 1 ──────────────────────────────────────────────┐
│  1. [指标搜索] 搜索该领域标准评价指标                     │
│  2. [基线实现] 写一个朴素版本作为 baseline               │
│  3. [基线评测] 用搜索到的指标评测 baseline，记录          │
│  4. [瓶颈分析] 分析热点 (profiling / 复杂度分析)         │
│  5. [优化方案] 提出优化策略 → 实现                       │
│  6. [优化评测] 同指标评测优化版                          │
│  7. [对比] baseline vs 优化版 对比记录                   │
│                                                        │
│  if 优化后提升 < 20% 或用户满意 → 结束                   │
│  else → Round 2 (回到步骤4，最多 3 轮)                  │
└────────────────────────────────────────────────────────┘
```

### 3.2 指标搜索 Prompt 模板

当需要搜索评价指标时，按以下模式搜索：

```
[WebSearch] "<领域> benchmark metric 2025 2026"
[WebSearch] "<工具/框架> performance evaluation standard"
[context7] 查询框架官方文档中的 benchmark 方法

如果涉及 AI/ML：
[WebSearch] "<任务类型> evaluation metrics"
[WebSearch] "<数据集> standard evaluation protocol"
```

**指标必须满足**：
- ✅ 可量化（返回一个数字）
- ✅ 可复现（同一条件下多人跑出相同结果）
- ✅ 有公认度（业界或学术界认可）
- ❌ 不要自创没有依据的指标

### 3.3 评测 Protocol

```
## 评测配置
- 硬件环境：(CPU/GPU/内存)
- 数据集：(名称/大小/来源)
- 指标：(指标名 + 计算方式)
- 运行次数：至少 3 次取平均

## 结果
- Baseline:  指标A=xxx, 指标B=xxx
- Optimized: 指标A=xxx, 指标B=xxx
- 提升:      +xx% / -xx%
```

### 3.4 迭代终止条件

| 条件 | 行为 |
|------|------|
| 提升 > 50% | 记录结论，结束 |
| 提升 20-50% | 可以继续一轮，也可以结束 |
| 提升 < 20% | 记录"已达边际效益"，结束 |
| 连续两轮无提升 | 强制结束 |
| 用户说"够了" | 立即结束 |

### 3.5 瓶颈分析 Protocol

必须做以下至少一种分析才能提出优化方案：

```
- 时间分析: cProfile / py-spy / timeit（Python）
- 内存分析: memory_profiler / tracemalloc
- 复杂度分析: 大 O 推算
- IO 分析: 磁盘/网络吞吐
- 如果是模型: FLOPs / 参数量 / 推理延迟
```

---

## 4. 步骤记录 (Execution Logging)

**铁律：每一步执行必须归档，不做完不记日志就不算完成。**

### 4.1 目录结构

```
.goo/
├── plan.json                     # 当前任务 DAG
├── eval-metrics.md               # 评价指标定义
├── logs/
│   ├── _summary.md               # 本轮执行汇总
│   ├── 2026-05-06T14:30:00_step-1_调研方案.md
│   ├── 2026-05-06T14:35:00_step-2_基线实现.md
│   └── 2026-05-06T15:10:00_step-4_评测对比.md
└── iterations/
    └── 2026-05-06_round-1_优化CSV解析器.md
```

### 4.2 单步日志模板

```markdown
# Step 1: 调研现有 CSV 解析方案

| 字段 | 值 |
|------|-----|
| **ID** | 1 |
| **时间** | 2026-05-06T14:30:00+08:00 |
| **状态** | ✅ Completed |
| **耗时** | 4m12s |

## 输入
- 无（初始步骤）

## 输出
- 确定了 3 个候选方案：csv (stdlib)、pandas、polars
- Benchmark 指标：吞吐量 (rows/s)、内存峰值 (MB)
- 选择 csv + memory-mapped IO 作为优化方向

## 关键决策
1. 选择 rows/s 作为主要吞吐指标 → 原因：业界 CSV benchmark 通用
2. 放弃 pandas → 原因：内存开销大，与本项目"高性能"目标冲突

## 问题记录
- 无
```

### 4.3 汇总日志模板

```markdown
# 执行汇总 — CSV 解析器

| Step | 名称 | 状态 | 耗时 |
|------|------|------|------|
| 1 | 调研方案 | ✅ | 4m12s |
| 2 | 基线实现 | ✅ | 3m05s |
| 3 | 优化实现 | ✅ | 8m30s |
| 4 | 评测对比 | ✅ | 2m10s |

**总体耗时**: 17m57s
**结论**: 优化版比基线快 3.2x，满足目标
```

### 4.4 优化迭代记录模板

```markdown
# 优化迭代 Round 1 — CSV 解析器

## 指标
- 吞吐量: rows/s
- 内存峰值: MB
- 搜索来源: WebSearch "CSV parsing benchmark standard"

## Baseline
- 吞吐: 125,000 rows/s
- 内存: 45 MB (100MB 文件)

## 瓶颈分析
- 热点: `csv.reader` 逐行解析 (占 78% 时间)
- IO: 未使用 buffer，系统调用频繁

## 优化方案
- 实现: mmap + 批量解析
- 改动文件: `src/parser/csv_optimized.py`

## 优化后
- 吞吐: 402,000 rows/s (+221%)
- 内存: 52 MB (+15%，可接受)

## 决策
- ✅ 提升 > 50%，结束迭代
- 记录到 `.goo/eval-metrics.md` 作为项目指标基准
```

### 4.5 eval-metrics.md 模板

```markdown
# 评价指标库

## CSV 解析
| 指标 | 定义 | 计算方式 |
|------|------|---------|
| 吞吐量 | rows/s | 总行数 / 解析耗时(秒) |
| 内存峰值 | MB | 解析过程中最大 RSS |

## [下一个领域]
| 指标 | 定义 | 计算方式 |
|------|------|---------|
| ... | ... | ... |
```

---

## 5. 技术规范 (Python 项目)

### 5.1 代码风格

- Python 3.10+，类型注解必须完整
- 函数/方法必须有 type hints（返回值 + 参数）
- 使用 `ruff` 做 lint（默认配置 + line-length=100）
- 注释原则：只写 WHY，不写 WHAT
- 文件名：小写+下划线

### 5.2 项目结构

```
AutoGoo/
├── CLAUDE.md
├── .goo/                    # 自动生成，已 gitignore
├── .gitignore
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── orchestrator/        # 编排器
│   │   ├── __init__.py
│   │   ├── engine.py        # 执行引擎
│   │   └── scheduler.py     # DAG 调度
│   ├── parser/              # 任务解析
│   │   ├── __init__.py
│   │   └── planner.py
│   └── evaluator/           # 评测模块
│       ├── __init__.py
│       └── metrics.py
├── skills/                  # Claude Code skills
└── tests/
    ├── __init__.py
    └── test_*.py
```

### 5.3 src/orchestrator/engine.py 约定

```python
# 所有可并行执行的任务必须实现这个接口
class TaskStep:
    id: int
    name: str
    depends_on: list[int]
    type: str  # "exec" | "optimize" | "eval"
    
    async def execute(self, context: dict) -> dict:
        """返回 {"status": "ok", "output": ..., "metrics": {...}}"""
        ...
```

---

## 6. 问答 / 快捷命令

| 用户说 | 行为 |
|--------|------|
| "开始任务 / run: / 做这个" | 进入[任务解析](#1-任务解析-task-parsing) → 执行 |
| "优化 / optimize" | 触发[优化迭代循环](#3-优化迭代循环-optimization-iteration) |
| "评测 / evaluate / benchmark" | 搜索指标 → 执行评测 → 记录 |
| "状态 / status / 进展" | 展示 `.goo/logs/_summary.md` |
| "日志 / logs" | 列出 `.goo/logs/` 下所有文件 |
| "重新规划 / replan" | 重新解析当前任务，生成新 plan.json |
| "继续 / continue" | 从上次中断的步骤继续执行 |
| "并行执行 / parallel" | 按 DAG 当前轮并行分发所有无依赖步骤 |
| "重试 / retry" | 重试失败的步骤 |

---

## 7. 端到端速览

各环节的具体模板见对应章节，以下是完整的执行流程示意：

```
用户: "实现一个高性能 CSV parser"

  ↓ [1. 任务解析]
  plan.json: 调研 → 基线 + 优化(并行) → 评测对比
               (识别"高性能" → step 3 标记 optimize)

  ↓ [2. 执行引擎]
  Round 1: [调研]
  Round 2: [基线实现] ──┐ (并行)
           [优化实现] ──┘
  Round 3: [评测对比]

  ↓ [3. 优化迭代]
  指标搜索 → Baseline评测 → 瓶颈分析 → 优化 → 对比
  125k→402k rows/s (+221%) → 结束

  ↓ [2.5.7 Obsidian Recorder]
  Goo-wiki/wiki/projects/csv-parser/  ← 步骤+任务笔记 (tag: auto-goo)
  Goo-wiki/wiki/concepts/parse/       ← 指标档案 (tag: auto-goo, metrics)
  Goo-wiki/log.md                     ← 活动日志
```
