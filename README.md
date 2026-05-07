# AutoGoo

自动化智能体编排框架。把"做这个"变成有序的工作流。

```bash
cc --plugin git+https://github.com/ZixiGu/AutoGoo.git
```

之后在任何 Claude Code 会话中：

```
/auto-goo 把这份 CSV 数据按地区汇总，生成报告
```

AutoGoo 会自动将任务解析为 DAG → 按依赖并行执行 → （可选）优化迭代 → 归档到 Goo-wiki。

---

## 快速开始 (Quick Start)

### 1. 安装插件

```bash
# 方式一：从 GitHub 安装（推荐）
cc --plugin git+https://github.com/ZixiGu/AutoGoo.git

# 方式二：本地路径安装（已 clone 仓库）
cc --plugin-dir /path/to/AutoGoo
```

### 2. 配置 SessionStart hooks（可选）

将以下配置加入项目 `.claude/settings.json`，实现启动时自动检测 Goo-wiki 和未完成任务：

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

### 3. 开始使用

在任何 Claude Code 会话中：

```
/auto-goo 用 Python 写一个快速排序，并优化性能
```

或直接下达自然语言任务，AutoGoo 会自动识别并启动工作流。

---

## 工作流

```
任务 → [解析] → plan.json(DAG) → [执行] → [归档]
                              ↘ (含优化) [指标搜索] → [基线] → [优化] → [对比]
```

| 阶段 | 做什么 |
|------|--------|
| **解析** | 识别交付物 → 逆向拆解为原子步骤 → 标注依赖 → 输出 plan.json |
| **执行** | 按 DAG 轮次分发 Subagent，同轮无依赖步骤并行执行 |
| **优化** | 搜索指标 → Baseline → 瓶颈分析 → 优化 → 评测对比 |
| **归档** | 执行记录转为 Obsidian 笔记，写入 Goo-wiki vault |

## 快捷命令

| 输入 | 行为 |
|------|------|
| `/auto-goo <任务>` | 启动完整工作流 |
| `开始任务 / run:` | 同 /auto-goo |
| `优化` | 启动优化迭代 |
| `评测 / benchmark` | 搜索指标 → 执行评测 |
| `状态 / status` | 显示当前进度 |
| `继续 / continue` | 从上次中断处继续 |

## 项目结构

```
.claude-plugin/             ← 插件入口
skills/auto-goo/            ← auto-goo 技能定义
  ├── SKILL.md                  工作流入口
  ├── references/               详细规范
  │   ├── setup.md              环境设置
  │   ├── task-parsing.md       任务解析
  │   ├── execution-engine.md   执行引擎
  │   ├── optimization-loop.md  优化循环
  │   ├── obsidian-archive.md   Obsidian 归档
  │   └── python-standards.md   Python 规范
  ├── examples/                 工作流示例
  ├── scripts/                  实用工具
  │   └── init-plan.sh          plan.json 生成器
  └── agents/                   Subagent 定义
agents/                 ← 归档 Subagent
commands/               ← /auto-goo 斜杠命令
CLAUDE.md               ← 项目专属指引
.goo/                   ← 自动生成的执行记录
```

## 要求

- Claude Code
- 工具权限：Read, Write, Edit, Bash, WebSearch, Agent
- （可选）Goo-wiki Obsidian vault 用于归档
