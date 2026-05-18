# AutoGoo 环境设置

## Goo-wiki Obsidian Vault

Goo-wiki 是归档笔记的目标 Obsidian vault。插件在运行时通过文件存在性检测 vault 是否可用。

**推荐初始化命令**：

```text
/auto-goo:goo-init
```

该命令支持用户级和项目级配置：

- `/auto-goo:goo-init --user` → `~/.auto-goo/config.json`
- `/auto-goo:goo-init --project` → `.goo/config.json`；当 Goo-wiki 可用时，询问是否更新项目 `CLAUDE.md` 的归档原则段落

底层实现是交互脚本：

```bash
SCRIPT="skills/auto-goo/scripts/goo-init.sh"
if [ ! -f "$SCRIPT" ]; then
  SCRIPT="$(find "${AUTO_GOO_PLUGIN_DIR:-$HOME}" -path '*/skills/auto-goo/scripts/goo-init.sh' -print -quit)"
fi
test -n "$SCRIPT" && bash "$SCRIPT"
```

脚本会询问作用域和 wiki 路径，默认路径为 `~/workspace/Goo-wiki`。初始化不需要 Agent 参与。
如果当前运行环境无法交互读取输入，必须先问用户作用域和 wiki 路径，并在问题中展示默认路径 `~/workspace/Goo-wiki`；用户不输入路径时使用默认路径。随后显式传入 `--user/--project` 与 `--wiki-dir <路径>`；不得默认写入项目配置，也不得在未展示默认路径的情况下静默使用默认 wiki 路径。

**路径解析优先级**：

1. 环境变量 `AUTO_GOO_WIKI_DIR`
2. 当前项目 `.goo/config.json` 中的 `wiki_dir`
3. 用户级 `~/.auto-goo/config.json` 中的 `wiki_dir`
4. 默认路径 `~/workspace/Goo-wiki`
5. fallback 归档目录 `.goo/obsidian/`

**默认检测路径**：

```
~/workspace/Goo-wiki/CLAUDE.md
```

各项目通过 `/auto-goo:goo-init` 或 CLAUDE.md 的 SessionStart hook 执行检测。vault 存在时归档到 `Goo-wiki/wiki/`，不存在则降级为 `.goo/obsidian/` fallback。

## 项目 CLAUDE.md 归档原则

项目级初始化使用 Goo-wiki 时，AutoGoo 会询问用户是否在项目根目录 `CLAUDE.md` 中追加或更新由 `AUTO-GOO-WIKI-ARCHIVE` marker 包裹的段落。该段落要求：

- 规划前先从 Goo-wiki 召回相关项目经验、概念页、周报和 `log.md`
- `goo-plan` 的 `.goo/plan.json` 最后保留 `归档到 Goo-wiki` 步骤
- 执行后归档目标、计划、证据、产物路径、验证结果、决策、问题处理和可复用经验
- Goo-wiki 不可用时写入 `.goo/obsidian/` fallback
- 归档内容必须服务下一次任务复用，而不是只做事后报告

该更新是幂等的，只替换 AutoGoo marker 内的内容，不覆盖项目已有指引。非交互场景默认不写，需传 `--update-claude-md` 明确写入；需要跳过时传 `--skip-claude-md`。

## 配置文件

用户级配置适合统一 wiki 路径和默认执行偏好；项目级配置适合覆盖单个 repo 的并发、归档或 wiki 设置。两者结构相同。

`~/.auto-goo/config.json` 或 `.goo/config.json` 示例：

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

### 自定义路径

可以用环境变量覆盖 wiki 路径：

```bash
export AUTO_GOO_WIKI_DIR="$HOME/workspace/Goo-wiki"
```

也可以在项目 `.claude/settings.json` 的 SessionStart hook 中修改检测命令：

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "ls <你的路径>/CLAUDE.md >/dev/null 2>&1 && echo '✓ Goo-wiki vault ready' || echo '⚠ Goo-wiki not found'"
      }]
    }]
  }
}
```

## 推荐 SessionStart hooks

以下 hooks 在每个会话启动时执行，建议加入项目 `.claude/settings.json`：

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [
        {
          "type": "command",
          "command": "ls ~/workspace/Goo-wiki/CLAUDE.md >/dev/null 2>&1 && echo '✓ Goo-wiki vault ready' || echo '⚠ Goo-wiki not found — 使用 .goo/obsidian/ fallback'"
        },
        {
          "type": "command",
          "command": "cat .goo/plan.json 2>/dev/null && echo '⚠ 发现未完成任务，输入 /auto-goo:goo-continue 可继续执行' || true"
        }
      ]
    }]
  }
}
```
