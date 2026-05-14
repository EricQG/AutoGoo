# 执行引擎 (Execution Engine)

## 核心原则

AutoGoo 的"并行"是 **task-level 并行**（多个独立 Subagent 同时执行），不是 thread-level 或 process-level 并行。每个步骤由独立的 Subagent 执行，通过 `.goo/logs/` 交换结果。

- 并行步骤必须无共享资源（文件、变量、状态）
- 结果通过日志文件传递，不通过内存
- 每个 Subagent 看到的是上游步骤的输出快照
- **plan.json 是唯一状态源**：派发、完成、失败均回写 plan.json

## 执行流程（槽位调度模型）

旧模型是"整层一起发 → 整层一起等 → 下一层"，存在三个问题：
- 同一层内快的 agent 完成了，下游步骤还得等慢的
- 无并发上限，10 个 agent 同时下发可能触发 API 限流
- 调度不区分优先级，关键路径步骤和边缘步骤同等对待

新模型：**固定并发槽位 + 动态就绪队列 + 连续下发**。

```
MAX_CONCURRENT = 6  (默认，可在 plan.json 顶层覆盖。上限不做硬限制，尽量多)

初始化:
  running = []       # 当前在跑的 agent 槽位
  ready_queue = []   # 就绪但等待槽位的步骤

主循环:
  while 有 pending 步骤 或 running 非空:
    1. 扫描就绪步骤
       - 选 status=pending 且 depends_on 全部 completed 的步骤
       - 按优先级排序 → 加入 ready_queue

    2. 填充空槽位
       while len(running) < MAX_CONCURRENT 且 ready_queue 非空:
         step = ready_queue.pop(0)
         更新 status="running", progress=0, agent_id, started_at → plan.json
         启动 Agent (run_in_background, 间隔 3-5s 错峰)
         running.append(step)

    3. 等待任一 Agent 完成
       任一 running agent 完成（或超时/失败）
         → 从 running 移除
         → 收集结果 → 写入 .goo/logs/
         → 更新 status="completed"(progress=100)/"failed" → plan.json
         → 立即回到步骤 1（该 agent 解锁的下游步骤可以马上入队）

    4. 心跳与进度巡检
       每 30s 检查 running 中 agent 的 heartbeat_at + progress
       heartbeat_at 超时 >= 5min → 标记 failed, 释放槽位
       progress 停滞不变超过 3 轮心跳 → 标记为 stuck，发出警告

所有步骤 completed 或无可执行步骤 → 结束
```

### 关键改进

| 旧模型 | 新模型 |
|--------|--------|
| 整层一起发 | 最多 6 个并发槽位 |
| 整层完成后才解锁下游 | agent 完成即解锁其下游，不等同层 |
| 无优先级 | 按扇出 + 预估耗时排序 |
| 同时下发竞争 API | 3-5s 间隔错峰下发 |
| 无并发上限 | MAX_CONCURRENT 软限制（尽量多） |
| 心跳只有时间戳 | 心跳带 progress (0-100)，/auto-goo:goo-status 展示进度条 |

### 优先级排序规则

ready_queue 中步骤按以下优先级排序（依次递减）：

1. **扇出度**（降序）— 该步骤解锁了多少个下游步骤。下游多的先跑，尽早暴露并行度
2. **预估耗时**（降序）— 慢的先跑，快的同时填充（流水线效应）
3. **同层剩余数**（升序）— 同一 original tier 中剩余未完成步骤少的优先

### 错峰下发

同一批次填充空槽位时，每个 agent 派发间隔 5-10 秒：

```
for step in batch:
   启动 Agent(step)
   if 不是本批次最后一个:
     等待 5-10 秒  # 避免 API 限流
```

### plan.json 实时回写

每步状态变更必须立即更新 plan.json：

| 时机 | 更新字段 |
|------|---------|
| 派发 Agent 前 | `status="running"`, `agent_id`, `started_at=now`, `heartbeat_at=now` |
| Agent 完成 | `status="completed"/"failed"`, `completed_at=now` |
| Agent 心跳 | `heartbeat_at=now`（agent 每 30s 自行更新） |

### MAX_CONCURRENT 配置

在 plan.json 顶层可覆盖：

```json
{
  "task": "...",
  "max_concurrent": 2,
  "steps": [...]
}
```

默认 6。调低（2-3）避免限流；调高（8-10）最大化并行度。不做硬限制。

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
2. **第一步：更新 plan.json** — 将自己的 heartbeat_at 和 progress=5 写入
3. **创建日志文件** `.goo/logs/{YYYY-MM-DDTHH-MM-SS}_step-{id}_{name}.md`，记录开始时间和任务概要
4. **每 30 秒更新 plan.json**：
   - `heartbeat_at` = 当前时间
   - `progress` = 0-100 的进度估算（已生成行数/估算总行数、已处理子图/总子图等）
   - 进度估算方法：任务开头在心里拆 3-5 个里程碑（如：读输入 10% → 核心逻辑 50% → 写输出 80% → 自查 95%），每过一个里程碑更新一次
5. 执行实现后**更新日志**，补充：关键决策、输出产物路径、耗时
6. **完成后回写 plan.json**：status="completed", progress=100, completed_at=now
7. 如果失败：status="failed"，在日志中记录失败原因
8. 日志必须包含：做了什么、关键决策、输出产物路径、耗时

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
5. **完成后回写 plan.json**：status="completed"
```

## 通用 Dispatch 流程

```
主循环每次迭代:
  1. 扫描 plan.json
     → 找出所有 status=pending 且 depends_on 全部 completed 的步骤
     → 按优先级排序（扇出度 > 预估耗时 > 同层剩余数）
     → 加入 ready_queue

  2. 填充槽位
     while running slots < MAX_CONCURRENT AND ready_queue 非空:
       step = ready_queue.pop(0)
       → 更新 plan.json: status="running", started_at=now
       → 构造 Subagent Prompt（含：任务描述、上游输出、交付要求、心跳+回写指令）
       → 启动 Agent (run_in_background)
       → 等待 3-5s（错峰）
       → running.append(step)

  3. 等待完成事件
     → 任一 agent 完成 → 从 running 移除
     → 回写 plan.json: status="completed"/"failed"
     → 写入 .goo/logs/
     → 立即回到步骤 1（刚完成步骤的下游可能已就绪）

  4. 心跳巡检（每 30s）
     → 检查 running 中每个 agent 的 heartbeat_at
     → 超时 >= 5min → 标记 failed，释放槽位
```

## 心跳机制

### 为什么需要心跳

后台 Agent 随主会话死亡（`/exit` 或超时时所有 run_in_background agent 被 kill）。没有心跳就无法区分"agent 死了"和"agent 还在跑"。

### 心跳规则

- Agent 启动后立即写第一次 heartbeat_at + progress=5
- 之后每 30 秒更新：`heartbeat_at` + **`progress` (0-100)**
- 进度估算：agent 在任务开头拆 3-5 个里程碑，每过一个里程碑更新进度
- 心跳通过 Bash 工具执行：`python3 -c "import json; ..."` 原地更新 plan.json

### 进度判断

| progress 状态 | 判断 |
|---------------|------|
| 0 | 刚启动，尚未开始实质工作 |
| 5-25 | 读输入、理解上下文阶段 |
| 30-70 | 核心实现阶段 |
| 75-95 | 收尾、自查、写日志 |
| 100 | 完成（与 status=completed 同步） |
| 停滞 >= 3 轮心跳 | 可能卡住，发出警告 |

### 心跳判断（恢复时使用）

| heartbeat_at 状态 | 判断 |
|-------------------|------|
| 距今 < 2 分钟 | Agent 可能仍在运行（如果会话还在） |
| 距今 >= 2 分钟 | Agent 已死亡（僵尸进程），可重新派发 |
| 为空（从未启动） | 步骤从未被执行 |

## 错误处理

| 情况 | 处理方式 |
|------|---------|
| Agent 执行失败 | 记录错误日志，重试 1 次 |
| 重试仍失败 | 标记 status="failed"，继续执行不依赖它的步骤 |
| 关键路径失败 | 通知用户，询问是否继续 |
| Agent 超时（>5 分钟无心跳） | 视为失败，按失败流程处理 |
| 会话中断（心跳停滞 >= 2min） | 恢复时检测到僵尸，重置为 pending 重新派发 |
| 部分成功 | 合并已成功的结果，标注失败步骤 |

## 结果合并

所有并行 Agent 完成后：
1. 收集每个 Agent 写入的 `.goo/logs/` 记录
2. 汇总到 `.goo/logs/_summary.md`
3. plan.json 已是最新状态，无需额外合并
4. 通知用户完成状态

## 上下文传递规则

| 上游产出类型 | 传递方式 | 示例 |
|-------------|---------|------|
| 代码文件 | 传递文件路径 | `/src/parser/baseline.py` |
| 数据文件 | 传递路径 + schema | `/data/benchmark_results.json` |
| 分析结论 | 直接写在 prompt 中 | "基线吞吐为 125k rows/s" |
| 模型权重 | 传递路径 + 指标 | `/models/checkpoint.pt, acc=0.92` |

## 并行分发检查清单

分发每个 Agent 前确认：

- [ ] MAX_CONCURRENT 未满（running < 3 或配置值）？
- [ ] 上一步派发距今 >= 5s（错峰间隔）？
- [ ] 步骤间真的没有数据依赖（与所有 running agent 无冲突）？
- [ ] 步骤间不会写同一个文件（与所有 running agent 无冲突）？
- [ ] 该 Agent 的 prompt 包含：任务描述 + 上游产物路径 + 回写 plan.json 指令？
- [ ] 该 Agent 知道往哪里写日志（`.goo/logs/`）？
- [ ] 日志写入逻辑独立于执行结果（即使失败也能写日志）？
- [ ] 下游扇出度已计算（用于优先级排序）？

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
