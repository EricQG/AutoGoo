# AutoGoo

[![Release](https://img.shields.io/badge/release-v0.1.0-blue)](#版本)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-black)](#安装)
[![Status](https://img.shields.io/badge/status-preview-orange)](#版本)

AutoGoo 是一个 Claude Code 插件，用于把开放式任务转成可追踪、可恢复、可归档的多 Agent 工作流。它会先从 Goo-wiki 召回已有项目知识，再把任务规划成 DAG，按依赖关系并行执行独立步骤，在需要时加入评测和优化循环，最后把新的经验归档回 Goo-wiki。

![AutoGoo 工作流](docs/assets/autogoo-workflow.svg)

## 亮点

- **DAG 优先规划**：执行前先把多步骤任务拆成明确依赖关系。
- **结构化 Markdown 输入**：把 README、TODO、issue 模板和设计文档当作任务载体，而不是默认当作普通文本处理。
- **对话方案沉淀**：把聊天中形成的方案、取舍、约束和验收标准写入 plan 或 Markdown，避免执行阶段依赖上下文记忆。
- **Goo-wiki 经验召回**：规划前读取已有项目页、概念页、周报和历史决策。
- **并行执行**：把无依赖冲突的步骤派发给隔离上下文的 subagent。
- **主 Agent 把关**：主 Agent 负责规划、上下文裁剪、调度、审查、冲突处理和最终验收；subagent 只执行被分配的步骤。
- **优化循环**：识别性能类任务，加入 benchmark、baseline、profiling 和优化对比。
- **持久知识归档**：把任务摘要、步骤证据、指标、决策和经验写回 Goo-wiki。
- **自改进工作流**：收集执行摩擦点，并通过 `/auto-goo:goo-improve` 进入插件优化流程。
- **命名空间命令**：所有 slash command 使用 `/auto-goo:goo-*`，避免污染命令列表。

## 安装

从 GitHub 直接安装：

```bash
cc --plugin git+https://github.com/ZixiGu/AutoGoo.git
```

或从本地 checkout 安装：

```bash
cc --plugin-dir /path/to/AutoGoo
```

安装后检查插件结构：

```bash
bash /path/to/AutoGoo/skills/auto-goo/scripts/check-plugin.sh
```

## 快速开始

先初始化用户级配置，再按需为具体项目初始化项目级配置：

```text
/auto-goo:goo-init --user
/auto-goo:goo-init --project
```

`goo-init` 由本地交互脚本驱动。它会询问配置作用域和 Goo-wiki 路径，默认提供 `~/workspace/Goo-wiki`，并直接写入配置文件，不派发 Agent。项目级初始化使用可用的 Goo-wiki vault 时，会创建项目归档根目录，并询问是否把 Goo-wiki 召回与归档要求写入项目 `CLAUDE.md` 的 AutoGoo marker 块。

只想先审阅 DAG，不立即执行时：

```text
/auto-goo:goo-plan 按地区汇总这份 CSV，并生成一份简短报告
```

从任意 Claude Code 会话启动完整工作流：

```text
/auto-goo:goo-start 按地区汇总这份 CSV，并生成一份简短报告
```

AutoGoo 会：

1. 检测 Goo-wiki vault，并召回相关项目经验。
2. 把请求解析成 `.goo/plan.json` DAG。
3. 使用并行 subagent 执行就绪步骤。
4. 在需要时运行 benchmark 和优化循环。
5. 把日志、决策、指标和经验归档回 wiki 笔记。
6. 收集流程问题，供后续自改进。

## 命令

| 命令 | 用途 |
| --- | --- |
| `/auto-goo:goo-init --user` | 创建用户级默认配置 `~/.auto-goo/config.json`。 |
| `/auto-goo:goo-init --project` | 创建项目级覆盖配置 `.goo/config.json`，并在 Goo-wiki 可用时创建项目归档根目录。 |
| `/auto-goo:goo-plan <任务>` | 召回 wiki 上下文并生成 `.goo/plan.json`，不执行。 |
| `/auto-goo:goo-start <任务>` | 启动完整 AutoGoo 工作流。 |
| `/auto-goo:goo-status` | 渲染当前 `.goo/plan.json` 进度面板。 |
| `/auto-goo:goo-continue` | 通过状态、产物和心跳检查恢复中断任务。 |
| `/auto-goo:goo-benchmark` | 执行指标发现、基线测量、profiling、优化和对比。 |
| `/auto-goo:goo-improve` | 回顾近期流程摩擦，生成插件改进建议。 |

自然触发词如 `开始任务`、`run:`、`状态`、`继续`、`评测`、`自改进` 也在 skill prompt 中定义；对外推荐优先使用命名空间 slash command。

## 只规划不执行

当你希望 AutoGoo 先召回上下文、生成执行计划，但暂时不改项目文件、不启动 subagent 时，使用：

```text
/auto-goo:goo-plan <任务>
```

该命令会写入可审阅、可恢复的 `.goo/plan.json`。如果旧 plan 已存在，AutoGoo 会先把旧文件归档到 `.goo/plans/history/`，再写入新的当前 plan。

Markdown 文件或片段会被按结构化任务输入解析：标题、checkbox、表格、代码块、路径、命令、约束和验收标准都会转换成规划信号。只有用户明确要求总结、润色或改写 Markdown 时，才按文本处理任务执行。

如果任务在对话中已经讨论出方案，`goo-plan` 还会把已确认方案、拒绝原因、用户偏好、硬约束和验收标准写入 `context_digest`；大段方案材料会优先落到 Goo-wiki 项目路径 `wiki/projects/<project-slug>/context/*.md`，并由 `context_artifacts` 引用。Goo-wiki 不可用时才降级到 `.goo/obsidian/<project-slug>/context/*.md`。后续执行不需要翻聊天记录，只读 plan、相关 Markdown、wiki 摘要和上游产物即可继续。

生成的 plan 应包含：

- `task`：用户原始任务或等价摘要。
- `wiki_context`：规划前召回的 Goo-wiki 来源和可复用知识。
- `context_digest`：当前对话中已确认的方案、约束、验收标准和未决问题。
- `context_artifacts`：可选，指向 Goo-wiki 项目路径下的 `context/*.md`、fallback `.goo/obsidian/<project-slug>/context/*.md` 或任务 Markdown。
- `steps`：有序 DAG 节点，包含 `id`、`tier`、`depends_on`、`type`、`status`、`progress` 和预期 `output`。
- `subagent`：每个步骤的执行角色，例如 `research`、`implementer`、`optimizer`、`evaluator`、`reviewer`、`recorder`。
- `max_concurrent`：计划中的并发执行上限。

审阅后可使用 `/auto-goo:goo-start <同一任务>` 执行完整流程，或用 `/auto-goo:goo-continue` 从当前 `.goo/plan.json` 恢复。

## Wiki 记忆循环

AutoGoo 把 Goo-wiki 当作项目记忆层，而不只是最终报告目录。每个工作流都有两个 wiki 触点：

1. **规划前召回**：读取与任务相关的项目页、概念笔记、周报和 `log.md`，提取可复用约束、失败经验、已验证命令、数据位置、指标口径和命名规范。
2. **执行后归档**：把最终任务笔记、步骤证据、指标结果、关键决策和后续经验写回 Goo-wiki，供未来 AutoGoo 任务复用。

如果 `~/workspace/Goo-wiki/CLAUDE.md` 不存在，AutoGoo 会降级到 `.goo/obsidian/`，并保持本地笔记结构一致。

Wiki 路径解析优先级：

1. `AUTO_GOO_WIKI_DIR`
2. 项目配置 `.goo/config.json` 的 `wiki_dir`
3. 用户配置 `~/.auto-goo/config.json` 的 `wiki_dir`
4. 默认路径 `~/workspace/Goo-wiki`
5. fallback 归档目录 `.goo/obsidian/`

建议先运行 `/auto-goo:goo-init --user` 写入机器级默认值，再在具体 repo 中运行 `/auto-goo:goo-init --project` 写入项目级覆盖。

## 配置

AutoGoo 同时读取用户级和项目级配置。项目配置覆盖用户配置，环境变量 `AUTO_GOO_WIKI_DIR` 会覆盖两者中的 wiki 路径。

用户级配置：

```text
~/.auto-goo/config.json
```

项目级配置：

```text
.goo/config.json
```

示例：

```json
{
  "version": 1,
  "wiki_dir": "/home/zixigu/workspace/Goo-wiki",
  "wiki": {
    "search_paths": [
      "wiki/projects",
      "wiki/concepts",
      "journal/weekly",
      "log.md"
    ]
  },
  "archive": {
    "enabled": true,
    "fallback_dir": ".goo/obsidian",
    "plan_history_dir": ".goo/plans/history",
    "project_slug": "<project-slug>",
    "project_dir": "wiki/projects/<project-slug>",
    "fallback_project_dir": ".goo/obsidian/<project-slug>",
    "git_remote_url": "https://github.com/<owner>/<repo>.git"
  },
  "execution": {
    "max_concurrent": 6,
    "heartbeat_seconds": 30,
    "stale_after_seconds": 120
  },
  "planning": {
    "recall_wiki": true,
    "require_wiki_context": false
  },
  "init": {
    "prompt_for_scope": true,
    "prompt_for_wiki_dir": true
  }
}
```

关键字段：

| 字段 | 含义 |
| --- | --- |
| `wiki_dir` | Goo-wiki vault 根路径。 |
| `wiki.search_paths` | 规划前需要检索的 wiki 区域。 |
| `archive.enabled` | 是否归档任务产物和经验。 |
| `archive.fallback_dir` | Goo-wiki 不可用时的本地 fallback 目录。 |
| `archive.plan_history_dir` | 历史 `.goo/plan.json` 快照目录。 |
| `archive.project_slug` | `wiki/projects/` 下的项目文件夹名。 |
| `archive.project_dir` | Goo-wiki 内的项目归档根路径，项目初始化时自动创建。 |
| `archive.fallback_project_dir` | Goo-wiki 不可用时的项目级本地归档根路径。 |
| `archive.git_remote_url` | 项目是 Git repo 时自动记录的 remote 地址；会同步写入 Goo-wiki 项目页。 |
| `execution.max_concurrent` | 最大并行 Agent 槽位数。 |
| `execution.heartbeat_seconds` | Agent 心跳间隔。 |
| `execution.stale_after_seconds` | 恢复时判定 running step 过期的阈值。 |
| `planning.recall_wiki` | 规划时是否复用 wiki 知识。 |
| `planning.require_wiki_context` | 缺少 wiki 上下文时是否阻塞规划。 |
| `init.prompt_for_scope` | 初始化时是否询问 user/project 作用域。 |
| `init.prompt_for_wiki_dir` | 初始化时是否询问 wiki 路径。 |

## 可选 Session Hooks

如果希望 Claude Code 在会话启动时检查 Goo-wiki 可用性和未完成 AutoGoo plan，可把下面内容加入项目级 `.claude/settings.json`：

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [
        {
          "type": "command",
          "command": "ls ~/workspace/Goo-wiki/CLAUDE.md >/dev/null 2>&1 && echo 'Goo-wiki vault ready' || echo 'Goo-wiki not found; using .goo/obsidian fallback'"
        },
        {
          "type": "command",
          "command": "cat .goo/plan.json 2>/dev/null && echo 'Unfinished AutoGoo plan found; run /auto-goo:goo-continue to resume' || true"
        }
      ]
    }]
  }
}
```

## 工作流模型

执行期间，AutoGoo 只把当前 `.goo/plan.json` 当作唯一状态源。历史 plan 会保存在 `.goo/plans/history/`，用于审计和回看；`goo-continue` 默认只从当前 plan 恢复，除非用户明确指定要恢复某个历史文件。

Subagent 默认使用隔离上下文：只拿当前步骤、`context_digest` 中相关决策、相关 wiki 约束、直接上游产物、允许读写路径，以及 plan/log/heartbeat 回写要求。它们不会收到完整主会话历史或无关 subagent 推理；需要共享的大段方案必须先整理成 Goo-wiki 项目路径下的 `context/*.md`，再通过路径传递。

| 阶段 | 输出 |
| --- | --- |
| Recall | 相关 Goo-wiki 笔记、历史决策、可复用命令、已知风险和项目约定。 |
| Parse | 任务目标、DAG 步骤、依赖边、优化标记。`/auto-goo:goo-plan` 在此阶段后停止。 |
| Execute | 步骤产物、结构化日志、重试状态、心跳。 |
| Optimize | 指标、基线、profiling 记录、优化实现和对比结果。 |
| Archive | `.goo/logs/` 记录，以及 Goo-wiki 项目/概念笔记。 |
| Improve | 流程摩擦摘要，以及针对插件 prompt、参考文档或设置的改进建议。 |

## 仓库结构

```text
.claude-plugin/             插件元数据
commands/                   /auto-goo:goo-* slash commands
skills/auto-goo/            goo-workflow skill 和参考文档
  SKILL.md                  工作流入口 prompt
  references/               执行、解析、归档、优化等详细说明
  examples/                 工作流示例
  scripts/                  校验和辅助脚本
  templates/                项目配置模板
agents/                     Subagent 定义
.goo/                       本地任务计划、日志和归档运行记录
```

## 运行要求

- 支持 plugin 的 Claude Code
- 工具：`Read`、`Write`、`Edit`、`Bash`、`WebSearch`、`Agent`
- 推荐：位于 `~/workspace/Goo-wiki` 的 Goo-wiki Obsidian vault

## 版本

当前版本：**v0.1.0**

这是一个 preview 版本，重点覆盖核心插件契约：

- 命名空间 `/auto-goo:goo-*` 命令
- 通过 `/auto-goo:goo-init` 初始化项目
- plan-only 和 full-run 两种工作流模式
- DAG 规划和执行规范
- 优化与 benchmark 工作流
- Goo-wiki 召回和归档约定
- 插件自改进循环
- 结构自检脚本

## 许可证

AutoGoo 使用 [MIT License](LICENSE) 发布。
