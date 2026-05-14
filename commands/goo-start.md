---
name: auto-goo:goo-start
description: 启动 AutoGoo 自动化工作流 — 将任务解析为 DAG，自动执行并归档
---

# /auto-goo:goo-start — 启动 AutoGoo 工作流

输入 `/auto-goo:goo-start <任务描述>` 启动完整工作流。

## 工作流阶段

1. **任务解析** — 将任务拆解为 DAG 步骤，输出 `.goo/plan.json`
2. **执行** — 按轮次并行/串行分发 Subagent
3. **优化**（如需要）— 指标搜索 → Baseline → 优化 → 评测对比
4. **归档** — 执行记录写入 Goo-wiki Obsidian vault

## 参数

任务描述支持自然语言，不限格式。AutoGoo 会自动解析目标、拆解步骤、标注依赖。

## 示例

```
/auto-goo:goo-start 用 Python 实现一个 CSV 解析器，支持大文件
/auto-goo:goo-start 优化项目中 JSON 序列化的性能
/auto-goo:goo-start 分析销售数据并按地区汇总
/auto-goo:goo-start 写一个斐波那契数列的单元测试
/auto-goo:goo-start 把这个 Markdown 文件转成 PDF 报告
```

## 备注

- 如果任务只有单步（如"转成 PDF"），不走完整工作流，直接执行
- 优化迭代默认最多 3 轮
- 日志保存在 `.goo/logs/`
