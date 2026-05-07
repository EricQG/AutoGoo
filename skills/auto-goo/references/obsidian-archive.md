# Obsidian 归档 (Goo-wiki Archiving)

每次任务执行后，Recorder Subagent 将执行记录转化为符合 Goo-wiki 规范的 Obsidian 笔记。

## 目录规则

不设独立 `auto-goo/` 目录，按任务所属领域放入对应目录，通过 `auto-goo` tag 区分来源。

**输出目录优先级**：
1. `Goo-wiki/wiki/projects/<project-slug>/`（Goo-wiki vault 存在时）
2. `.goo/obsidian/<project-slug>/`（fallback，仅本地归档）

**路径检测**：检查 `/home/zixigu/workspace/Goo-wiki/CLAUDE.md` 是否存在。不存在则降级为 fallback。

## Goo-wiki 约定

- 按项目放入 `wiki/projects/<project-slug>/` 下
- 指标类知识放入 `wiki/concepts/<domain>/`
- YAML frontmatter 使用标准格式（type, title, status, tags, aliases, date）
- 所有笔记追加 `tags: [auto-goo, <domain>]`（至少 2 个 tag，auto-goo 标记来源）
- 笔记的文件名和 tag 从用户输入的 task 语义推导，而非从执行的具体操作命名
- 文件名使用小写连字符（`lowercase-with-hyphens.md`）
- 默认使用中文
- 每次任务完成后向 `Goo-wiki/log.md` 追加活动日志
- 不写入 `raw/` 目录（原始来源不可变）
- 成熟度 status: `seed` → `developing` → `stable`
- 使用 `[[Wikilink]]` 建立双向链接

## 笔记类型

| 笔记类型 | 路径 | Tag | 频率 |
|---------|------|-----|------|
| 任务总览 | `wiki/projects/<slug>/<task>.md` | `[auto-goo, <domain>]` | 每次任务 |
| 步骤笔记 | `wiki/projects/<slug>/<task>-step-<id>.md` | `[auto-goo, <domain>, step]` | 每步一次 |
| 迭代记录 | `wiki/projects/<slug>/<task>-round-<n>.md` | `[auto-goo, <domain>, optimization]` | 每轮优化 |
| 指标档案 | `wiki/concepts/<domain>/<task>-metrics.md` | `[auto-goo, metrics]` | 追加累积 |
| 活动日志 | `log.md` | `## [YYYY-MM-DD] auto-goo \| <task>` | 每次任务 |

## Recorder Prompt 模板

当步骤完成或任务结束时，按以下模式派发 Recorder：

```
你是一个 AutoGoo Obsidian Recorder Subagent。

## 任务
将以下执行记录格式化为符合 Goo-wiki 规范的 Obsidian 笔记。

## 输入数据
{step_log_content}

## Goo-wiki 规范（必须遵守）
1. 不设独立 auto-goo 目录，按项目领域放入对应路径：
   - 任务/步骤/迭代 → wiki/projects/<project-slug>/
   - 指标 → wiki/concepts/<domain>/
2. 所有笔记 tags 必须包含 auto-goo + 至少一个领域 tag
3. Tag 和文件名从用户输入的**任务目的**推导，不从实现命名
4. YAML frontmatter 格式：type, title, domain, status, tags, date, aliases
5. type 取值：concept（步骤/指标）、project（任务总览）
6. status 取值：seed / developing / stable
7. 文件名使用小写连字符
8. 默认使用中文
9. 用 [[wiki/projects/<project-slug>/xxx|显示名]] 格式的 wikilink
10. 数字和指标用表格呈现
11. 任务完成后向 Goo-wiki/log.md 追加一条活动日志
12. 不要写入 raw/ 目录
13. 输出目录优先级：Goo-wiki/wiki/ > .goo/obsidian/（fallback）
14. 子步骤内容内联在主任务笔记中，用 --- 分隔，不拆为独立文件
```

## log.md 追加格式

```markdown
## [{{YYYY-MM-DD}}] auto-goo | {{task_name}}

执行 {{step_count}} 步，耗时 {{total_duration}}。含优化迭代 {{round_count}} 轮。
项目页：[[wiki/projects/<project-slug>/<task-name>|<task_name>]]
```

## 命名规范

- 文件名/标签从任务目的推导：CLAUDE.md 优化 → `claude-md-优化` / `[auto-goo, claude-md-optimization]`
- 文件名小写连字符，子步骤内联在主笔记中用 `---` 分隔
- 同一领域任务使用相同 slug，创建新目录前检查是否已有相关领域目录
- fallback（Goo-wiki 不存在时）：`.goo/obsidian/<slug>/`，跳过 log.md
