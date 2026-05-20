# Obsidian 归档 (Goo-wiki Archiving)

AutoGoo 以 Goo-wiki 作为项目记忆层：任务开始前读取已有知识，任务结束后将新经验归档回 wiki。Recorder Subagent 负责把执行记录转化为符合 Goo-wiki 规范的 Obsidian 笔记。

## 知识闭环

AutoGoo 的 wiki 流程分成两段：

1. **执行前召回**：读取相关项目页、概念页、周报和 `log.md`，提取历史决策、已验证命令、数据路径、指标口径、失败经验和后续计划。
2. **执行后归档**：把本次任务的目标、计划、对话中固化的方案决策、步骤证据、产物、验证结果、指标、问题处理和可复用经验写回 Goo-wiki，并补齐与既有 Markdown 页面之间的 `[[Wikilink]]`，让 Obsidian 关联图谱随任务增长。

归档不是附加项，也不是孤立报告，而是为了让下一次 AutoGoo 任务能沿着项目页、概念页、问题页、周报和日志之间的链接继续推进。

## 目录规则

不设独立 `auto-goo/` 目录，按任务所属领域放入对应目录，通过 `auto-goo` tag 区分来源。

**输出目录优先级**：
1. `<wiki_dir>/<archive.project_dir>/`（Goo-wiki vault 存在时，通常是 `Goo-wiki/wiki/projects/<project-slug>/`）
2. `<archive.fallback_project_dir>/`（fallback，仅本地归档，通常是 `.goo/obsidian/<project-slug>/`）

**路径检测**：按 `AUTO_GOO_WIKI_DIR` → `.goo/config.json.wiki_dir` → `~/.auto-goo/config.json.wiki_dir` → `~/workspace/Goo-wiki` 解析 wiki 目录，并检查 `<wiki_dir>/CLAUDE.md` 是否存在（详见 `setup.md`）。项目归档根目录由 `.goo/config.json.archive.project_dir` 指定；不存在则降级为 fallback。

## Goo-wiki 约定

- 按项目放入 `archive.project_dir` 指向的项目根目录下，默认是 `wiki/projects/<project-slug>/`
- 指标类知识放入 `wiki/concepts/<domain>/`
- 周期性复盘和项目状态参考 `journal/weekly/`，但任务产物不直接写入周报
- YAML frontmatter 使用标准格式（type, title, status, tags, aliases, date）
- 所有笔记追加 `tags: [auto-goo, <domain>]`（至少 2 个 tag，auto-goo 标记来源）
- 笔记的文件名和 tag 从用户输入的 task 语义推导，而非从执行的具体操作命名
- 文件名使用小写连字符（`lowercase-with-hyphens.md`）
- 默认使用中文
- 每次任务完成后向 `Goo-wiki/log.md` 追加活动日志
- 如果项目是 Git repo，必须在项目页或任务总览笔记中记录 git remote 地址；优先读取 `.goo/config.json.archive.git_remote_url`，缺失时用 `git remote get-url origin` 或第一个 remote 兜底
- 不写入 `raw/` 目录（原始来源不可变）
- 成熟度 status: `seed` → `developing` → `stable`
- 使用 `[[Wikilink]]` 建立双向可发现的链接；任何新任务页都不能成为孤立页面

## 关联图谱规则

Recorder 写入或更新 Markdown 时，必须同时维护页面之间的语义链接，目标是让 Obsidian graph/backlinks 能回答“这个任务属于哪个项目、复用了哪些知识、产出了哪些经验、影响哪些后续问题”。

为减少 token 消耗，Recorder 优先调用通用脚本生成紧凑链接上下文，而不是直接读取大量 Markdown：

```bash
python3 "${AUTO_GOO_ROOT:-$CLAUDE_PLUGIN_ROOT}/skills/auto-goo/scripts/wiki-graph-assist.py" \
  --wiki-dir "$WIKI_DIR" \
  --project-slug "<project-slug>" \
  --query "<task title and key terms>" \
  --task-page "wiki/projects/<project-slug>/<task>.md" \
  --max-pages 12
```

脚本只输出相关页面、候选 `[[Wikilink]]`、少量标题和片段。任务页写好后，可用 `--update-index --append-log` 机械维护项目入口和 `log.md` 链接。

**归档前检查**：
- 在 `wiki.search_paths` 范围内检索同项目、同领域、同数据集、同配置、同命令、同错误信息和同指标口径的既有页面。
- 优先识别项目入口 `wiki/projects/<project-slug>/index.md`、相关任务页、概念页、问题页、周报、`log.md` 和 `context_artifacts`。
- 如果已存在同主题页面，优先更新或链接到既有页面；只有任务语义确实独立时才创建新页面。

**归档时必须建立的链接**：
- 新任务页链接回项目入口：`[[wiki/projects/<project-slug>/index|项目名]]`。
- 项目入口新增或更新“最近记录 / 相关任务 / 当前状态”中的任务页链接。
- 任务页链接到本次复用的 `wiki_context`、`context_artifacts`、关键概念页、问题页、指标页、数据/配置说明页和必要周报。
- 可复用经验应写入任务页的“可复用经验”小节，必要时链接到独立 lessons/concept 页面；相关 concept/lessons 页面也应链接回代表性任务页。
- `log.md` 的活动日志必须链接到任务页；如果任务改变项目状态，项目入口也要能从正文链接到这条任务记录。

**链接质量约束**：
- 不为了图谱密度链接所有出现过的词，只链接能帮助后续召回、规划、复盘或溯源的页面。
- 不手工维护无限增长的反链清单；反链交给 Obsidian。页面正文只保留少量高价值“相关链接”。
- 纯路径、文件名、命令和错误文本如果对应已有说明页，应同时给出 `[[...]]` 链接；没有对应页面时保留代码格式路径即可。
- fallback `.goo/obsidian/` 归档也按同样链接结构写 Markdown，方便未来迁移回 Goo-wiki。

## 笔记类型

| 笔记类型 | 路径 | Tag | 频率 |
|---------|------|-----|------|
| 任务总览 | `wiki/projects/<slug>/<task>.md` | `[auto-goo, <domain>]` | 每次任务 |
| 步骤笔记 | `wiki/projects/<slug>/<task>-step-<id>.md` | `[auto-goo, <domain>, step]` | 每步一次 |
| 迭代记录 | `wiki/projects/<slug>/<task>-round-<n>.md` | `[auto-goo, <domain>, optimization]` | 每轮优化 |
| 指标档案 | `wiki/concepts/<domain>/<task>-metrics.md` | `[auto-goo, metrics]` | 追加累积 |
| 经验沉淀 | `wiki/projects/<slug>/<task>-lessons.md` 或任务页小节 | `[auto-goo, lessons]` | 有复用价值时 |
| 活动日志 | `log.md` | `## [YYYY-MM-DD] auto-goo \| <task>` | 每次任务 |

## Recorder Prompt 模板

当步骤完成或任务结束时，按以下模式派发 Recorder：

```
你是一个 AutoGoo Obsidian Recorder Subagent。

## 任务
将以下执行记录格式化为符合 Goo-wiki 规范的 Obsidian 笔记。

## 输入数据
{step_log_content}
{wiki_context}

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
9. 用 [[wiki/projects/<project-slug>/xxx|显示名]] 格式的 wikilink，并避免产生孤立页面
10. 数字和指标用表格呈现
11. 记录本次任务复用了哪些 wiki 经验，以及新增了哪些可复用经验
12. 记录 `context_digest` 中的关键方案、取舍、用户约束和验收标准；如果有 `context_artifacts`，用路径或 wikilink 引用
13. 如果项目是 Git repo，在项目页或任务总览笔记的 `Project Metadata` / `项目元信息` 小节写入 git remote 地址；优先使用 `.goo/config.json.archive.git_remote_url`
14. 任务完成后向 Goo-wiki/log.md 追加一条活动日志，日志必须链接到任务页
15. 不要写入 raw/ 目录
16. 输出目录优先级：Goo-wiki/wiki/ > .goo/obsidian/（fallback）
17. 子步骤内容内联在主任务笔记中，用 --- 分隔，不拆为独立文件
18. 写入前检索并链接相关项目页、概念页、问题页、周报、context_artifacts 和历史任务页
19. 写入后更新项目入口 index.md，使项目入口能链接到本次任务页或最新状态
20. 如新增 concept/lessons/metrics 页面，必须从任务页链接过去，并在新页面链接回 1-3 个代表性任务页或项目入口
```

## log.md 追加格式

```markdown
## [{{YYYY-MM-DD}}] auto-goo | {{task_name}}

执行 {{step_count}} 步，耗时 {{total_duration}}。含优化迭代 {{round_count}} 轮。
项目页：[[wiki/projects/<project-slug>/<task-name>|<task_name>]]
Git: {{git_remote_url_or_empty}}
复用经验：{{reused_knowledge_count}} 条；新增经验：{{new_lessons_count}} 条。
```

## 命名规范

- 文件名/标签从任务目的推导：CLAUDE.md 优化 → `claude-md-优化` / `[auto-goo, claude-md-optimization]`
- 文件名小写连字符，子步骤内联在主笔记中用 `---` 分隔
- 同一领域任务使用相同 slug，创建新目录前检查是否已有相关领域目录
- fallback（Goo-wiki 不存在时）：`.goo/obsidian/<slug>/`，跳过 log.md
