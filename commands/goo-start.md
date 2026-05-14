---
name: auto-goo:goo-start
description: 启动 AutoGoo 完整工作流 — 召回 wiki 经验、生成 DAG、执行、验证并归档
---

# /auto-goo:goo-start — 启动 AutoGoo 工作流

输入 `/auto-goo:goo-start <任务描述>` 启动完整工作流。若只想生成计划、不执行，请使用 `/auto-goo:goo-plan`。

## 工作流阶段

1. **Wiki 经验召回** — 读取已有项目知识和历史经验
2. **任务解析** — 将任务拆解为 DAG 步骤，输出 `.goo/plan.json`
3. **执行** — 按轮次并行/串行分发 Subagent
4. **优化**（如需要）— 指标搜索 → Baseline → 优化 → 评测对比
5. **归档** — 执行记录和新增经验写入 Goo-wiki

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
