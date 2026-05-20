---
name: auto-goo:goo-usage
description: 显示 Claude Code token 和 usage 监控面板 — 多色可视化终端仪表盘
---

```bash
auto_goo_root="${AUTO_GOO_ROOT:-${CLAUDE_PLUGIN_ROOT:-$HOME/workspace/AutoGoo}}"
script="$auto_goo_root/skills/auto-goo/scripts/goo-usage.py"
interval="${GOO_USAGE_INTERVAL:-30}"

# ── Detect available terminal emulator ──
detect_terminal() {
    for cmd in gnome-terminal xfce4-terminal konsole xterm alacritty kitty tilix terminator; do
        if command -v "$cmd" &>/dev/null; then
            echo "$cmd"
            return
        fi
    done
    return 1
}

# ── Launch in separate terminal with watch ──
launch_watch() {
    local term
    term=$(detect_terminal) || { echo "No terminal emulator found, running inline"; return 1; }
    local watch_cmd="watch -n $interval -c -t python3 '$script' --once --tab '${1:-overview}'"

    case "$term" in
        gnome-terminal)
            gnome-terminal -- bash -c "$watch_cmd; echo 'Press Enter to close...'; read" &
            ;;
        xfce4-terminal)
            xfce4-terminal -e "bash -c '$watch_cmd; echo Press Enter to close...; read'" &
            ;;
        konsole)
            konsole -e bash -c "$watch_cmd; echo 'Press Enter to close...'; read" &
            ;;
        xterm)
            xterm -e bash -c "$watch_cmd; echo 'Press Enter to close...'; read" &
            ;;
        alacritty)
            alacritty -e bash -c "$watch_cmd; echo 'Press Enter to close...'; read" &
            ;;
        kitty)
            kitty bash -c "$watch_cmd; echo 'Press Enter to close...'; read" &
            ;;
        tilix)
            tilix -e "bash -c '$watch_cmd; echo Press Enter to close...; read'" &
            ;;
        terminator)
            terminator -e "bash -c '$watch_cmd; echo Press Enter to close...; read'" &
            ;;
        *)
            echo "Unknown terminal: $term, running inline"
            return 1
            ;;
    esac
    echo "Launched usage monitor in $term (refresh: ${interval}s)"
}

# ── Ask user ──
echo "Open goo-usage in separate terminal with watch? [y/N]"
read -r REPLY
if [[ "$REPLY" =~ ^[Yy]$ ]]; then
    if launch_watch "${GOO_USAGE_TAB:-overview}"; then
        exit 0
    fi
fi

# ── Run inline (interactive TUI) ──
python3 "$script" --interval "$interval" $ARGS
```

## 仪表盘

4 个 Tab，默认打开 Overview：

| Tab | 快捷键 | 内容 |
|-----|--------|------|
| **Overview** | `1` | 今日总览：token 总量、消息数、会话数、token 组成（渐变色条）、模型分布、24 小时活动 sparkline、峰值时段、燃耗率、Top 项目 |
| **Projects** | `2` | 按项目拆分：渐变色条展示各项目 token 占比，消息数、会话数、cost |
| **Models** | `3` | 模型对比：每个模型的 token 量、消息数、效率(tok/msg)、I/O 比、缓存命中率、cost per message |
| **History** | `4` | 7 天趋势：sparkline 总览、逐日渐变色条、3 日趋势箭头（▲/▼ + 变化%）、7 日汇总 |

## 操作

- `←` `→` 或 `Tab` 切换 Tab
- `1` `2` `3` `4` 直接跳转
- `q` 退出
- `--once` 打印一次后退出（不进入 watch 模式）
- `--interval N` 设置刷新间隔（默认 30s）

## 内置价格

脚本内建常见 Claude 模型的官方定价（USD/1M tokens），无需手动传 `--price`：

- claude-opus-4-7: $15/$75 input/output
- claude-sonnet-4-6: $3/$15
- claude-haiku-4-5: $0.80/$4

传 `--no-builtin-pricing` 禁用内建价格；传 `--pricing FILE` 或 `--price MODEL=X,Y,Z` 使用自定义价格。

## 用户意图映射

历史/趋势 → `--tab history`，项目分布 → `--tab projects`，模型分析 → `--tab models`，只看一次 → `--once`。
