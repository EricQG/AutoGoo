---
name: auto-goo:goo-start
description: 启动 AutoGoo 完整工作流 — 召回 wiki 经验、生成 DAG、执行、验证并归档
---

# /auto-goo:goo-start — 启动 AutoGoo 工作流

输入 `/auto-goo:goo-start <任务描述>` 启动完整工作流。若只想生成计划、不执行，请使用 `/auto-goo:goo-plan`。

## 工作流阶段

1. **Wiki 经验召回** — 读取已有项目知识和历史经验
2. **对话方案固化** — 把当前对话中已经确认的方案、约束、取舍和验收标准写入 `.goo/plan.json.context_digest`；大段内容写入 Goo-wiki 项目路径 `wiki/projects/<project-slug>/context/*.md`，Goo-wiki 不可用时降级到 `.goo/obsidian/<project-slug>/context/*.md`
3. **任务解析** — 将任务拆解为 DAG 步骤；写入新的 `.goo/plan.json` 前，先把已有 plan 归档到 `.goo/plans/history/`
4. **执行前自检** — 确认每个待执行 step 不依赖主会话隐含上下文，只依赖 plan、Markdown/context artifact、wiki 摘要和上游产物
5. **执行** — 按轮次并行/串行分发 Subagent
6. **优化**（如需要）— 指标搜索 → Baseline → 优化 → 评测对比
7. **归档** — 执行记录和新增经验写入 Goo-wiki

## 参数

任务描述支持自然语言，不限格式。AutoGoo 会自动解析目标、拆解步骤、标注依赖。

如果当前目录已经存在 `.goo/plan.json`，且用户没有提供新的任务描述，优先从当前 plan 执行；如果用户提供了新的补充方案或约束，先归档旧 plan，再把补充内容更新进 `context_digest` / `context_artifacts` 后执行。

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
- 执行阶段不能依赖聊天记录里的隐含方案；发现信息缺失时先补 plan 或写 Goo-wiki 项目路径 `context/*.md`
- 优化迭代默认最多 3 轮
- 日志保存在 `.goo/logs/`
