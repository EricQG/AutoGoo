---
name: auto-goo:goo-improve
description: 启动 AutoGoo 插件自改进流程 — 汇总近期执行问题，生成插件优化方案
---

# /auto-goo:goo-improve — 插件自改进

分析近期执行日志中的流程问题，汇总高频摩擦点，生成针对插件文件（SKILL.md、references、settings）的改进方案。

## 执行流程

1. 读取 `.goo/logs/` 中近 5 个任务的 `## 流程问题` 记录
2. 聚类分析，识别高频问题（出现 >= 2 次）
3. 对每个高频问题定位根因文件
4. 生成具体修改方案
5. 用户确认后执行修改
6. 记录到 `.goo/improvements.log`

## 示例

```
/auto-goo:goo-improve
优化AutoGoo
自改进
```

## 备注

- 仅建议，不改动不经用户确认
- 详见 `skills/auto-goo/references/self-improvement.md`
