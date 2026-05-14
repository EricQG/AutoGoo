# AutoGoo

[![Release](https://img.shields.io/badge/release-v0.1.0-blue)](#release)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-black)](#installation)
[![Status](https://img.shields.io/badge/status-preview-orange)](#release)

AutoGoo is a Claude Code plugin that turns an open-ended request into a traceable,
multi-agent workflow: plan the task as a DAG, execute independent steps in parallel,
run optional optimization loops, and archive the result for later review.

![AutoGoo workflow](docs/assets/autogoo-workflow.svg)

## Highlights

- **DAG-first planning**: decomposes multi-step tasks into explicit dependencies before execution.
- **Parallel execution**: dispatches dependency-free steps to subagents instead of running everything serially.
- **Optimization loop**: detects performance-oriented tasks and adds benchmark, baseline, profiling, and comparison stages.
- **Obsidian-ready archive**: records task logs and optional Goo-wiki notes so decisions do not disappear after a session.
- **Self-improving workflow**: collects friction points and routes them into `/auto-goo:goo-improve`.
- **Namespaced commands**: exposes plugin commands as `/auto-goo:goo-*`, keeping the slash-command list tidy.

## Installation

Install directly from GitHub:

```bash
cc --plugin git+https://github.com/ZixiGu/AutoGoo.git
```

Or install from a local checkout:

```bash
cc --plugin-dir /path/to/AutoGoo
```

Verify the plugin structure after installation:

```bash
bash /path/to/AutoGoo/skills/auto-goo/scripts/check-plugin.sh
```

## Quick Start

Start a workflow from any Claude Code session:

```text
/auto-goo:goo-start Summarize this CSV by region and generate a short report.
```

Chinese task descriptions work naturally:

```text
/auto-goo:goo-start 把这份 CSV 数据按地区汇总，生成报告
```

AutoGoo will:

1. parse the request into a `.goo/plan.json` DAG,
2. execute ready steps with parallel subagents,
3. run benchmark and optimization loops when needed,
4. archive logs and notes,
5. collect workflow issues for future improvement.

## Commands

| Command | Purpose |
| --- | --- |
| `/auto-goo:goo-start <task>` | Start a full AutoGoo workflow. |
| `/auto-goo:goo-status` | Render the current `.goo/plan.json` progress dashboard. |
| `/auto-goo:goo-continue` | Resume an interrupted workflow with status, artifact, and heartbeat checks. |
| `/auto-goo:goo-benchmark` | Run metric discovery, baseline measurement, profiling, optimization, and comparison. |
| `/auto-goo:goo-improve` | Review recent workflow friction and generate plugin improvement suggestions. |

Natural triggers such as `开始任务`, `run:`, `状态`, `继续`, `评测`, and `自改进` are also documented in the skill prompt, but the slash-command surface is intentionally namespaced.

## Optional Session Hooks

Add this to a project-level `.claude/settings.json` if you want Claude Code to check Goo-wiki availability and unfinished AutoGoo plans at session start:

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

## Workflow Model

AutoGoo keeps `.goo/plan.json` as the single source of truth during execution.

| Phase | Output |
| --- | --- |
| Parse | Task goal, DAG steps, dependency edges, optimization markers. |
| Execute | Step artifacts, structured logs, retry state, heartbeats. |
| Optimize | Metrics, baseline, profiler notes, improved implementation, comparison. |
| Archive | `.goo/logs/` records and optional Goo-wiki Obsidian notes. |
| Improve | Friction summaries and proposed edits for plugin prompts, references, or settings. |

## Repository Layout

```text
.claude-plugin/             Plugin metadata
commands/                   /auto-goo:goo-* slash commands
skills/auto-goo/            goo-workflow skill and references
  SKILL.md                  Workflow entry prompt
  references/               Detailed execution, parsing, archive, and optimization docs
  examples/                 Example workflows
  scripts/                  Validation and helper scripts
agents/                     Subagent definitions
.goo/                       Local task plans, logs, and archived runs
```

## Requirements

- Claude Code with plugin support
- Tools: `Read`, `Write`, `Edit`, `Bash`, `WebSearch`, `Agent`
- Optional: a Goo-wiki Obsidian vault at `~/workspace/Goo-wiki`

## Release

Current release: **v0.1.0**

This is a preview release focused on the core plugin contract:

- namespaced `/auto-goo:goo-*` commands,
- DAG planning and execution guidance,
- optimization and benchmark workflow,
- Obsidian/Goo-wiki archive conventions,
- plugin self-improvement loop,
- structural self-check script.

## License

AutoGoo is released under the [MIT License](LICENSE).

