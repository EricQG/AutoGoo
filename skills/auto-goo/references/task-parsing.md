# 任务解析 (Task Parsing)

## 解析流程

1. **识别最终交付物** — "用户最终要拿到什么？脚本、模型、报告还是系统？"
2. **逆向拆解** — 从目标倒推："要交付这个，需要先有什么？" 持续追问直到拆成原子步骤
3. **标注依赖关系** — 步骤 A 必须在 B 之前完成 → A `depends_on` B
4. **识别优化标记** — 包含"性能/速度/延迟/吞吐/效率/内存/GPU/耗时" → `type: "optimize"`
5. **范围约束** — 每个步骤目标严格取自任务描述，不添加未要求的功能
6. **输出 plan.json**

## 解析 Prompt 模板

按以下模板在脑中执行（不需要输出给用户看）：

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

## plan.json Schema

```json
{
  "task": "<任务描述>",
  "created_at": "YYYY-MM-DDTHH-MM-SS",
  "max_concurrent": 6,
  "steps": [
    {
      "id": 1,
      "tier": 1,
      "name": "<步骤名>",
      "description": "<做什么>",
      "depends_on": [],
      "type": "exec",
      "status": "pending",
      "progress": 0,
      "output": "<产物路径>",
      "agent_id": null,
      "heartbeat_at": null,
      "started_at": null,
      "completed_at": null
    }
  ]
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `id` | 全局唯一数字 ID |
| `tier` | 执行轮次，同一轮内无依赖的步骤可并行 |
| `name` | 简短动词短语 |
| `description` | 做什么，含完整上下文。需要外部包时末尾标注 `[dep: <包名>]` |
| `depends_on` | 前置步骤 ID 列表，空数组表示无依赖 |
| `type` | `exec` / `optimize` / `eval` |
| `output` | 预期产物文件路径，用于恢复时检测是否已完成 |
| `status` | `pending` → `running` → `completed` / `failed`。主会话派发/检测到完成时更新 |
| `progress` | 0-100 整数，agent 每次心跳时更新。pending 为 0，completed 为 100 |
| `agent_id` | 执行该步骤的 Agent ID，派发时填写，完成后保留用于审计 |
| `heartbeat_at` | 最后一次心跳时间戳。agent 每 30s 更新，主会话通过此字段判断 agent 是否存活 |
| `started_at` | 步骤开始时间戳 |
| `completed_at` | 步骤完成时间戳 |
| `estimated_time` | 可选，如 "5min" |

### 时间戳格式

统一使用 `YYYY-MM-DDTHH-MM-SS`（例：`2026-05-06T14-30-00`），避免文件名中冒号冲突。

## 依赖与并行判断规则

| 情况 | 策略 |
|------|------|
| `depends_on` 为空且互不引用 | 并行分发 |
| `depends_on` 相同 | 前驱完成后并行 |
| `depends_on` 有传递链 | 按拓扑序串行 |
| 一个步骤的输出是另一个的输入 | 串行（即使忘记标注也要推断） |

### 执行顺序提取算法

```
1. 找出所有 status=pending 且 depends_on 全部 completed 的步骤 → 当前轮
2. 当前轮内步骤 → 并行分发；跨轮 → 串行
3. 每完成一轮，更新 plan.json 中对应步骤的 status
4. 重复直到所有步骤 completed 或无可执行的 pending 步骤
```

### 步骤状态生命周期

```
pending ──→ running ──→ completed
  │            │
  │            └──→ failed（重试 1 次后仍失败）
  │
  └── 跳过（depends_on 中有 failed 且非关键路径）

心跳保活：running 状态的步骤每 30s 更新 heartbeat_at。
恢复时如果 heartbeat_at 超过 2 分钟未更新 → 视为僵尸进程，可重新派发。
```

### 恢复时完成度判断优先级

1. `status = "completed"` → 跳过
2. `status = "running"` 且 `heartbeat_at` 在 2 分钟内 → 等待或跳过（agent 仍在跑）
3. `status = "running"` 且 `heartbeat_at` 超过 2 分钟 → 检查 output 文件是否存在
   - 产物文件存在且内容完整 → 标记为 completed
   - 产物文件不存在/不完整 → 重置为 pending，重新派发
4. `status = "pending"` 且 depends_on 全部 completed → 正常执行

## Plan 拆分决策

核心原则：**预估单会话跑不完就拆**。大 plan 提供全局 DAG 视图，但执行层面小 plan 更可靠。

### 大 plan vs 小 plan

| | 大 plan | 小 plan |
|---|---------|---------|
| 步数 | 6-20 步 | 2-4 步 |
| 会话 | 预期跨多个会话，需 `/auto-goo:goo-continue` 恢复 | 一次会话内跑完，无需恢复 |
| 产物传递 | 通过 plan.json + 产物文件路径 | 通过产物文件路径（或内存） |
| 适用场景 | 目标清晰、依赖关系已完全推演、可以一次性画出完整 DAG | 探索性任务、下一步依赖上一步结果才能决定方向 |

### 何时拆

以下任一条件满足，就应该拆成多个小 plan：

1. **预估总耗时 > 30 分钟** — 超过单会话安全窗口，大概率中断
2. **步骤数 > 8** — DAG 拓扑超过 3 层，后半段 agent 可能还没轮到会话就结束了
3. **中间产物是人工判断点** — 比如"先跑个基线看看效果再决定怎么优化"，不要预判结果往下串
4. **后半段步骤依赖前半段产物质量** — 如果 Tier 1 产物可能不合格，Tier 2-3 就是浪费

### 拆分方法

从大 plan 的 DAG 中切出当前可执行的前 1-2 层：

```
大 plan（14 步，7 层）:
  Tier 1: A, B, C ──→  小 plan 1: A, B, C（一次会话跑完）
  Tier 2: D, E, F, G ──→ 小 plan 2: D, E, F, G（拿到 1 的产物后启动）
  Tier 3: H, I ──→  小 plan 3: ...
  ...
```

每个小 plan 结束后：
- 产物文件落地
- plan.json 标记 completed
- 用户验收产物质量
- 启动下一个小 plan

### 何时不拆（用大 plan）

- 任务规模 <= 5 步，30 分钟内能跑完
- 依赖链很长但每步都很短（< 2min），总时长可控
- 用户明确要求"一次性全自动执行，不要中断问我"

### 大 plan 的安全网

如果必须用大 plan（跨会话），依赖三重恢复机制：
- `status` 字段追踪每步完成状态
- `heartbeat_at` 区分僵尸/存活 agent
- `output` 产物文件存在性兜底检测
