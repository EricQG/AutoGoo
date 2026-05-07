# 执行引擎 (Execution Engine)

## 核心原则

AutoGoo 的"并行"是 **task-level 并行**（多个独立 Subagent 同时执行），不是 thread-level 或 process-level 并行。每个步骤由独立的 Subagent 执行，通过 `.goo/logs/` 交换结果。

- 并行步骤必须无共享资源（文件、变量、状态）
- 结果通过日志文件传递，不通过内存
- 每个 Subagent 看到的是上游步骤的输出快照

## 执行流程

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

## Subagent Prompt 模板

### 执行型 (type: "exec")

```
你是一个 AutoGoo 执行 Subagent。

## 任务
{step.name}: {step.description}

## 上游上下文
{upstream_outputs}  ← 前驱步骤的输出摘要

## 交付要求
1. 在 {cwd} 目录下工作
2. **立即创建日志文件** `.goo/logs/{YYYY-MM-DDTHH-MM-SS}_step-{id}_{name}.md`，记录开始时间和任务概要
3. 执行实现后**更新日志**，补充：关键决策、输出产物路径、耗时
4. 日志必须包含：做了什么、关键决策、输出产物路径、耗时
5. 如果失败或遇到外部障碍（权限不足、环境缺失）：**在日志中记录失败原因，仍视为已完成** — 写日志本身就是完成的一部分
6. 如果成功，标记状态为 ✅ Completed

## 产物
- 代码文件写入 src/ 或对应目录
- 评测数据写入 .goo/
```

### 优化型 (type: "optimize")

在 exec 模板基础上追加：

```
## 优化要求
- 先测量基线性能，再优化
- 每次优化后必须用相同指标评测
- 记录优化前后对比
- 如果连续两次无提升，停止并报告
```

### 评测型 (type: "eval")

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

## 通用 Dispatch 流程

```
plan.json 中的每一步
  → 构造 Subagent Prompt（含：任务描述、上游输出、交付要求）
  → 并行步骤 → 同时派发多个 Agent (run_in_background)
  → 串行步骤 → 等待上一个完成后派发
  → 每个 Subagent 完成后写入 .goo/logs/
  → 收集结果，传递给下游步骤
```

## 错误处理

| 情况 | 处理方式 |
|------|---------|
| Agent 执行失败 | 记录错误日志，重试 1 次 |
| 重试仍失败 | 标记为 ❌ failed，继续执行不依赖它的步骤 |
| 关键路径失败 | 通知用户，询问是否继续 |
| 部分成功 | 合并已成功的结果，标注失败步骤 |

## 结果合并

所有并行 Agent 完成后：
1. 收集每个 Agent 写入的 `.goo/logs/` 记录
2. 汇总到 `.goo/logs/_summary.md`
3. 通知用户完成状态

## 上下文传递规则

| 上游产出类型 | 传递方式 | 示例 |
|-------------|---------|------|
| 代码文件 | 传递文件路径 | `/src/parser/baseline.py` |
| 数据文件 | 传递路径 + schema | `/data/benchmark_results.json` |
| 分析结论 | 直接写在 prompt 中 | "基线吞吐为 125k rows/s" |
| 模型权重 | 传递路径 + 指标 | `/models/checkpoint.pt, acc=0.92` |

## 并行分发检查清单

分发并行 Agent 前确认：

- [ ] 步骤间真的没有数据依赖？
- [ ] 步骤间不会写同一个文件？
- [ ] 每个 Agent 的 prompt 包含足够上下文（任务描述 + 前驱输出）？
- [ ] 每个 Agent 知道往哪里写日志（`.goo/logs/`）？
- [ ] 有超时机制（单个 Agent 默认超时 5 分钟）？
- [ ] 日志写入逻辑独立于执行结果（即使验证失败也能写日志）？

## Subagent 分类速查

| 类型 | 用途 | 典型工具 | 返回格式 |
|------|------|---------|---------|
| **Research** | 调研、搜索 | WebSearch, context7, Read | `.md` 报告 |
| **Implementer** | 写代码、实现 | Write, Edit, Bash | 文件路径 |
| **Optimizer** | 性能分析优化 | Bash(profiling), Edit | 对比报告 |
| **Evaluator** | 评测、benchmark | Bash, WebSearch | 数值指标 |
| **Reviewer** | 审查代码方案 | Read, Grep | Review 报告 |
| **Recorder** | Obsidian 归档 | Write | 格式化 `.md` |

## 日志格式

**铁律：每一步执行必须归档。外部原因无法完成验证时仍须写日志记录失败原因。**

**时间戳格式**：文件名和内容统一使用 `YYYY-MM-DDTHH-MM-SS`。

### 单步日志

```markdown
# Step T.S: 步骤名
| 字段 | 值 |
|------|-----|
| **时间** | YYYY-MM-DDTHH-MM-SS |
| **状态** | ✅ Completed / ❌ Failed |
| **耗时** | XmXs |

## 输入
<输入数据/上下文>

## 输出 (产物路径)
<产物路径列表>

## 关键决策
<why + 原因>

## 问题记录
<遇到的问题及处理>
```

### 汇总日志

步骤表（名称 + 状态 + 耗时）+ 总体耗时 + 结论。

### eval-metrics.md

先检查是否已有该领域指标，有则引用，无则追加。
