# Obsidian Recorder

将 AutoGoo 执行日志转化为符合 Goo-wiki 规范的 Obsidian 笔记。

## 职责

- 读取 `.goo/logs/` 下的步骤执行记录
- 格式化为 Obsidian 兼容 Markdown（YAML frontmatter + wikilinks）
- 写入 `Goo-wiki/wiki/` 对应目录（fallback: `.goo/obsidian/`）
- 追加 `Goo-wiki/log.md` 活动日志

## 调用方式

由 AutoGoo 执行引擎在以下时机调用：
1. 每步完成后 → 生成步骤笔记
2. 全部步骤完成后 → 生成任务总览 + 更新指标档案

## Goo-wiki 规范

- 不设独立 `auto-goo/` 目录，按项目领域散入
- 所有笔记 `tags` 必须包含 `auto-goo`
- 步骤/任务/迭代 → `Goo-wiki/wiki/projects/<slug>/`
- 指标 → `Goo-wiki/wiki/concepts/<domain>/`
- 文件名：小写连字符
- 默认中文
- 使用 `[[wiki/projects/<slug>/file|显示名]]` 格式的 wikilink

## 输入格式

```json
{
  "type": "step" | "task" | "iteration" | "metrics",
  "project_slug": "csv-parser",
  "domain": "parse",
  "data": { ... }
}
```

## 输出映射

| 输入类型 | 目标路径 | Frontmatter type |
|---------|---------|-----------------|
| step | `wiki/projects/<slug>/<task>-step-<id>.md` | concept |
| task | `wiki/projects/<slug>/<task>.md` | project |
| iteration | `wiki/projects/<slug>/<task>-round-<n>.md` | concept |
| metrics | `wiki/concepts/<domain>/<task>-metrics.md` | concept |

## Fallback

当 `/home/zixigu/workspace/Goo-wiki/` 不存在时：
- 目标前缀改为 `.goo/obsidian/`
- 不写 `log.md`
- 其余规范相同
