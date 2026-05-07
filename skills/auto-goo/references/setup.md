# AutoGoo 环境设置

## Goo-wiki Obsidian Vault

Goo-wiki 是归档笔记的目标 Obsidian vault。插件在运行时通过文件存在性检测 vault 是否可用。

**默认检测路径**：

```
~/workspace/Goo-wiki/CLAUDE.md
```

各项目通过 CLAUDE.md 的 SessionStart hook 执行检测。vault 存在时归档到 `Goo-wiki/wiki/`，不存在则降级为 `.goo/obsidian/` fallback。

### 自定义路径

在项目 `.claude/settings.json` 的 SessionStart hook 中修改检测命令：

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
          "command": "cat .goo/plan.json 2>/dev/null && echo '⚠ 发现未完成任务，输入 continue 可继续执行' || true"
        }
      ]
    }]
  }
}
```
