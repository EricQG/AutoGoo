---
name: auto-goo:goo-init
description: 初始化 AutoGoo 配置 — 支持用户级 ~/.auto-goo/config.json 和项目级 .goo/config.json
---

# /auto-goo:goo-init — 初始化配置

第一次使用 AutoGoo 时，可以初始化用户级默认配置；在具体项目里也可以初始化项目级覆盖配置。

```text
/auto-goo:goo-init
```

## 作用域

| 命令 | 写入位置 | 用途 |
| --- | --- | --- |
| `/auto-goo:goo-init --user` | `~/.auto-goo/config.json` | 当前用户的全局默认配置，适合统一 wiki 路径和执行偏好 |
| `/auto-goo:goo-init --project` | `.goo/config.json`，可选更新 `CLAUDE.md` | 当前项目的局部覆盖配置；Goo-wiki 可用时询问是否写入项目归档原则 |
| `/auto-goo:goo-init` | 交互提问 | 先询问配置到用户级还是项目级，再继续询问 wiki 路径 |

## 行为

该命令必须直接运行初始化脚本，不派发 Agent。slash command 的当前工作目录通常是用户项目，不一定是插件目录；运行前必须先定位脚本路径：

```bash
SCRIPT="skills/auto-goo/scripts/goo-init.sh"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$(find "${AUTO_GOO_PLUGIN_DIR:-$HOME}" -path '*/skills/auto-goo/scripts/goo-init.sh' -print -quit)"
fi
test -n "$SCRIPT" && bash "$SCRIPT" <用户选择的作用域>
```

如果 Claude Code 当前 Bash 环境无法交互读取输入，不要替用户默认选择 `--project`，也不要默默使用默认 wiki 路径；应先问两个问题：

1. 配置作用域：`--user` 还是 `--project`
2. Goo-wiki 路径：向用户展示默认路径 `~/workspace/Goo-wiki`；用户不输入或选择默认时就使用该路径，也可输入自定义路径

例如用户选择 `--user` 且不输入路径（使用默认路径）时，必须运行：

```bash
test -n "$SCRIPT" && bash "$SCRIPT" --user --wiki-dir ~/workspace/Goo-wiki
```

例如用户选择 `--project` 且输入自定义路径时，必须运行：

```bash
test -n "$SCRIPT" && bash "$SCRIPT" --project --wiki-dir /path/to/Goo-wiki
```

带参数示例：

```bash
SCRIPT="skills/auto-goo/scripts/goo-init.sh"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$(find "${AUTO_GOO_PLUGIN_DIR:-$HOME}" -path '*/skills/auto-goo/scripts/goo-init.sh' -print -quit)"
fi
test -n "$SCRIPT" && bash "$SCRIPT" --user
test -n "$SCRIPT" && bash "$SCRIPT" --project --wiki-dir ~/workspace/Goo-wiki
test -n "$SCRIPT" && bash "$SCRIPT" --project --wiki-dir ~/workspace/Goo-wiki --update-claude-md
test -n "$SCRIPT" && bash "$SCRIPT" --project --wiki-dir ~/workspace/Goo-wiki --skip-claude-md
```

脚本行为：

1. **选择作用域** — 用户级或项目级；未传 `--user/--project` 时交互提问
2. **创建配置目录** — 用户级确保 `~/.auto-goo/`；项目级确保 `.goo/`
3. **读取已有配置** — 如果目标配置已存在，先展示当前配置并询问是否更新
4. **配置 Wiki 路径** — 必须向用户提供默认路径 `~/workspace/Goo-wiki`；用户不输入则使用默认路径，也允许用户输入自定义路径，并按优先级解析：
   - `AUTO_GOO_WIKI_DIR`
   - 项目级 `.goo/config.json` 的 `wiki_dir`
   - 用户级 `~/.auto-goo/config.json` 的 `wiki_dir`
   - 默认 `~/workspace/Goo-wiki`
5. **检测 Wiki 可用性** — 检查 `<wiki_dir>/CLAUDE.md`
6. **写入配置** — 生成目标配置文件
7. **项目归档原则** — `--project` 且 Goo-wiki 可用时，询问用户是否幂等更新项目 `CLAUDE.md`，加入 Goo-wiki 召回与归档要求；非交互场景默认不写，需传 `--update-claude-md` 明确写入；如需明确跳过，传 `--skip-claude-md`
8. **提示 hooks** — 展示推荐的 `.claude/settings.json` SessionStart hooks，由用户决定是否复制/合并

## 默认配置

```json
{
  "version": 1,
  "wiki_dir": "~/workspace/Goo-wiki",
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
    "fallback_dir": ".goo/obsidian"
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

## 输出要求

- 不覆盖已有 `.goo/config.json`，除非用户明确确认
- 不覆盖已有 `~/.auto-goo/config.json`，除非用户明确确认
- 不删除任何已有 `.goo/` 内容
- `--project` 且 Goo-wiki 可用时，必须先询问用户是否更新 `CLAUDE.md`；用户同意后只追加或更新由 AutoGoo marker 包裹的归档原则段落，不重写其他内容
- 不借助 Agent 执行初始化；只运行定位到的 `skills/auto-goo/scripts/goo-init.sh`
- 用户回答了 `--user` 或 `--project` 后，必须把该参数传给脚本
- 用户确认或输入 wiki 路径后，必须把 `--wiki-dir <路径>` 传给脚本
- 如果 Goo-wiki 不存在，保留配置并提示将使用 `.goo/obsidian/` fallback
- 最终输出用户级、项目级和最终生效配置摘要
