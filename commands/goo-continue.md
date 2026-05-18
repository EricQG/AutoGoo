---
name: auto-goo:goo-continue
description: 从中断处继续执行 AutoGoo 任务 — 读取 .goo/plan.json 的三重检测（状态+文件+心跳）恢复未完成步骤
---

# /auto-goo:goo-continue — 继续执行任务

从上次中断处继续执行。读取 `.goo/plan.json`，用三重检测判断每步真实状态，从未完成的步骤开始按 DAG 拓扑重新执行。

`goo-continue` 的执行依据只能是当前 `.goo/plan.json`、`context_artifacts` 指向的 Goo-wiki/Markdown、Goo-wiki 摘要、`.goo/logs/` 和上游产物路径。不要依赖当前 Claude Code 会话还记得之前讨论过什么。

如果恢复时用户补充了新方案、约束或验收标准，先把旧 `.goo/plan.json` 归档到 `.goo/plans/history/`，再把新信息写入 `context_digest` 或 Goo-wiki 项目路径 `wiki/projects/<project-slug>/context/*.md`；Goo-wiki 不可用时写入 `.goo/obsidian/<project-slug>/context/*.md`，之后再继续执行。

## 恢复检测流程（按优先级）

对 plan.json 中每一个 step：

### 1. status = "completed" → 直接跳过

plan.json 已标记完成，无需额外检查。

### 2. status = "running" → 三重检测

```
heartbeat_at 距今 < 2 分钟？
  → YES: Agent 可能仍在运行。检查当前会话是否有对应后台任务
    → 有: 等待其完成
    → 无(跨会话恢复): 检查产物文件是否存在
      → 产物存在且非空: 标记为 completed，继续
      → 产物不存在: 重置为 pending，重新派发
  → NO(>= 2 分钟): Agent 已死亡
    → 检查产物文件是否存在
      → 产物存在且非空: 标记为 completed（agent 完成后来不及回写 plan.json）
      → 产物不存在: 重置为 pending，重新派发
```

### 3. status = "failed" → 判断是否关键路径

- 非关键路径（不阻塞其他 pending 步骤）→ 跳过
- 关键路径（阻塞后续步骤）→ 询问用户是否重试

### 4. status = "pending" → 正常执行

检查 depends_on 是否全部 completed，满足则加入当前执行轮。

## 产物文件存在性检测

对每个 step 的 `output` 字段指定的路径，执行：

```bash
# 对于 .py 文件，还需检查是否有实质内容（非空、非纯注释）
test -f "<output_path>" && [ "$(wc -l < "<output_path>")" -gt 5 ]
```

产物文件存在 + 行数 > 5 → 视为步骤已完成（即使 plan.json 未更新）。

## 执行流程

1. 读取 `.goo/plan.json`
2. 对每个 step 按上述优先级判断真实状态
3. 更新 plan.json（修复僵尸状态为 completed 或 pending）
4. 找出所有 status=pending 且 depends_on 全部 completed 的步骤
5. 检查待执行步骤是否可仅凭 plan/Markdown/wiki 摘要执行；不合格则先补全 plan
6. 按 tier 分组，同 tier 内并行派发
7. 按 AutoGoo 标准执行流程继续（Phase 2-4）

## 示例

```
/auto-goo:goo-continue
```

输出示例：
```
检测 plan.json (14 步):
  1. schemas.py        status=running, heartbeat=3min前 → 僵尸, 产物存在 → 标记 completed
  2. bbox_utils.py     status=running, heartbeat=3min前 → 僵尸, 产物存在 → 标记 completed
  3. constraints.py    status=running, heartbeat=3min前 → 僵尸, 产物存在 → 标记 completed
  4. annotation.py     status=running, heartbeat=3min前 → 僵尸, 产物不存在 → 重置 pending
  5. gen_p1.py         status=running, heartbeat=3min前 → 僵尸, 产物不存在 → 重置 pending
  ...

已修复 3 个僵尸状态，可恢复 4 个步骤
继续执行 tier 2 (步骤 4-7)...
```

## 备注

- 如果所有步骤已完成，提示"没有未完成的任务"
- 关键路径上的失败步骤会询问是否跳过继续
- `heartbeat_at` 为空且 status=running 的步骤：说明派发时写了 tier-X-start.json 但 agent 从未真正启动 → 直接重置为 pending
