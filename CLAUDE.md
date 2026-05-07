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

完整工作流定义在 **AutoGoo plugin** 中：

```
用户任务 → [任务解析] → plan.json(DAG) → [执行引擎] → 记录归档
                                    ↓ (若含优化标记)
                           [优化迭代循环] → [指标搜索] → 评测 → 对比记录
```

各阶段详细规范：
- **SKILL.md** — `skills/auto-goo/SKILL.md` — 工作流入口
- **任务解析** — `skills/auto-goo/references/task-parsing.md`
- **执行引擎** — `skills/auto-goo/references/execution-engine.md`
- **优化循环** — `skills/auto-goo/references/optimization-loop.md`
- **Obsidian 归档** — `skills/auto-goo/references/obsidian-archive.md`
- **Python 规范** — `skills/auto-goo/references/python-standards.md`

## 快捷命令

| 用户说 | 行为 |
|--------|------|
| "开始任务 / run: / 做这个" | 任务解析 → 执行 |
| "优化 / optimize" | 启动优化迭代循环 |
| "评测 / evaluate / benchmark" | 搜索指标 → 评测 → 记录 |
| "状态 / status / 进展" | 展示 `.goo/logs/_summary.md` |
| "日志 / logs" | 列出 `.goo/logs/` 下所有文件 |
| "重新规划 / replan" | 重新解析当前任务 |
| "继续 / continue" | 从上次中断的步骤继续 |
| "并行执行 / parallel" | 按 DAG 当前轮并行分发 |
| "重试 / retry" | 重试失败的步骤 |

## 流程自省与持续改进

AutoGoo 的 CLAUDE.md 本身也需要持续改进。每次执行过程中遇到的摩擦、歧义、缺失都应当被记录。

### 问题记录格式

在任务日志的末尾追加 `## 流程问题` 小节：

```markdown
## 流程问题
1. <问题描述> — <建议改进方向>
2. <问题描述> — <建议改进方向>
```

### 定期回顾

- 每执行 3-5 个任务后，回顾 `## 流程问题` 记录
- 对高频出现的问题，更新 CLAUDE.md 对应章节或 plugin 的 references/
