---
name: auto-goo:goo-plan
description: 只生成 AutoGoo 执行计划 — 召回 Goo-wiki 经验并输出 .goo/plan.json，不派发执行
---

# /auto-goo:goo-plan — 只规划，不执行

输入 `/auto-goo:goo-plan <任务描述>` 生成可审阅的 AutoGoo 计划。

## 行为

1. **Wiki 经验召回** — 检索 Goo-wiki 中相关项目页、概念页、周报和 `log.md`
2. **输入形态识别** — 判断输入是普通任务、Markdown 任务包、已有 plan、issue/PR 描述还是日志片段
3. **任务解析** — 将任务拆解为 DAG 步骤
4. **对话方案固化** — 抽取当前对话中已经形成的方案、取舍、约束、验收标准和用户明确偏好，写入 `context_digest`；内容过长时写入 Goo-wiki 项目路径 `wiki/projects/<project-slug>/context/<timestamp>-planning-context.md` 并在 plan 中引用
5. **上下文注入** — 把可复用经验写入 `wiki_context`，把对话方案写入 `context_digest` 或 `context_artifacts`
6. **归档任务补齐** — 默认在 DAG 最后追加 Wiki 归档步骤，依赖所有最终交付步骤
7. **历史计划归档** — 如果 `.goo/plan.json` 已存在，先复制到 `.goo/plans/history/plan-<timestamp>.json`
8. **计划落盘** — 输出或更新 `.goo/plan.json`
9. **等待确认** — 不派发 Subagent，不执行文件修改

## Markdown 任务输入

如果用户传入 Markdown 文件或片段，先按结构化任务读取：

- 标题层级表示任务主题、阶段或依赖分层。
- checkbox、编号列表和 TODO 表示候选步骤。
- 代码块、路径、命令和错误日志表示执行约束或验证依据。
- "目标/约束/验收/风险/产物/下一步"等小节必须转成 plan 约束。

不要把 Markdown 默认理解为"整理文本"。只有用户明确说要总结、润色、改写或重新排版 Markdown 时，才生成文本处理计划。

## 对话方案固化

如果用户在当前对话里已经讨论过方案、备选路线、关键约束或验收口径，`goo-plan` 必须把这些信息沉淀到持久载体，避免后续执行依赖主会话上下文。

- 简短信息写入 `.goo/plan.json.context_digest`，至少包含 `decisions`、`constraints`、`acceptance_criteria`、`open_questions`。
- 长方案、会议纪要或 prompt 草案优先写入 Goo-wiki 项目路径 `wiki/projects/<project-slug>/context/<timestamp>-planning-context.md`，并在 `.goo/plan.json.context_artifacts` 中引用；Goo-wiki 不可用时才降级写入 `.goo/obsidian/<project-slug>/context/`。
- 每个 step 的 `description` 必须自包含，不使用"按上面方案"、"参考前文"、"照刚才说的"这类隐含引用。
- 如果需要沉淀为长期项目经验，同时在归档步骤中要求写入 Goo-wiki；执行前不能只靠聊天记录理解任务。

## 适用场景

- 任务风险较高，需要先审计划
- 任务跨多个会话，想先确认 DAG 边界
- 需要确认 AutoGoo 是否正确复用了 Goo-wiki 项目经验
- 输入是 README、设计文档、TODO 清单或 issue 模板，需要先抽取真实执行任务
- 只想获得执行路线，不希望立即改代码或跑命令

## 示例

```text
/auto-goo:goo-plan 优化 KiCad VLM QA 生成流程，并复用已有 v3/v4 经验
/auto-goo:goo-plan 规划一个 CSV 分析报告工作流
```

## 输出要求

- `.goo/plan.json` 必须包含 `wiki_context`
- `.goo/plan.json` 必须包含 `context_digest`；没有额外对话方案时也写 `{"found": false, "decisions": [], "constraints": [], "acceptance_criteria": [], "open_questions": []}`
- 如果存在大段方案材料，必须包含 `context_artifacts`，用文件路径引用 Goo-wiki 项目路径下的 `context/*.md` 或相关任务 Markdown；Goo-wiki 不可用时引用 `.goo/obsidian/<project-slug>/context/*.md`
- 写入新的 `.goo/plan.json` 前，必须把已有 `.goo/plan.json` 原样归档到 `.goo/plans/history/`
- 每个步骤必须包含 `output`，便于后续 `/auto-goo:goo-continue` 恢复
- 每个步骤必须包含 `subagent`，明确执行角色：`research` / `implementer` / `optimizer` / `evaluator` / `reviewer` / `recorder`
- `steps` 最后必须包含 Wiki 归档任务，默认名称为 `归档到 Goo-wiki`，依赖所有非归档叶子步骤
- 如果没有找到相关 wiki 经验，写入 `wiki_context.found=false`
- 最终向用户展示简洁计划摘要和主要风险

## 下一步

计划确认后，用户可以运行：

```text
/auto-goo:goo-start <同一任务>
```

或让 AutoGoo 从当前 `.goo/plan.json` 继续执行。
