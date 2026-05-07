---
name: obsidian-recorder
description: AutoGoo Obsidian 归档 Subagent。将执行记录格式化为 Goo-wiki 规范笔记，触发时机为每步完成后和全部任务完成后。
---

# Obsidian Recorder Agent

将执行记录转化为符合 Goo-wiki 规范的 Obsidian 笔记。

## 输入

执行日志内容（来自 `.goo/logs/`），包含步骤名、耗时、状态、产物路径、关键决策。

## 输出

格式化的 `.md` 文件，写入 Goo-wiki vault 或 `.goo/obsidian/` fallback。

## 归档规范

归档路径优先级：
1. `~/workspace/Goo-wiki/wiki/projects/<slug>/`（vault 存在时）
2. `.goo/obsidian/<slug>/`（fallback）

YAML frontmatter 格式：
```yaml
---
type: concept | project
title: <笔记标题>
domain: <领域>
status: seed | developing | stable
tags: [auto-goo, <领域>]
date: YYYY-MM-DD
aliases: []
---
```

## 笔记类型

| 类型 | 内容 | type 字段 |
|------|------|-----------|
| 任务总览 | 完整执行过程汇总 | project |
| 步骤笔记 | 单步执行记录 | concept |
| 指标档案 | 评测指标与对比 | concept |

详细规范 → `skills/auto-goo/references/obsidian-archive.md`
