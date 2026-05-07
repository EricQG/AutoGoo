---
name: auto-goo
description: 启动 AutoGoo 自动化工作流 — 将任务解析为 DAG，自动执行并归档
---

# /auto-goo — 启动 AutoGoo 工作流

输入 `/auto-goo <任务描述>` 启动完整工作流。

工作流执行以下阶段：

1. **任务解析** — 将任务拆解为 DAG 步骤，输出 `.goo/plan.json`
2. **执行** — 按轮次并行/串行分发 Subagent
3. **优化**（如需要）— 指标搜索 → Baseline → 优化 → 评测对比
4. **归档** — 执行记录写入 Goo-wiki Obsidian vault

示例：

```
/auto-goo 用 Python 实现一个 CSV 解析器，支持大文件
/auto-goo 优化项目中 JSON 序列化的性能
/auto-goo 分析销售数据并按地区汇总
```
