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
.claude-plugin/     ← 插件入口
skills/auto-goo/    ← auto-goo 技能定义
  ├── SKILL.md         工作流入口
  └── references/      详细规范
commands/           ← 斜杠命令
CLAUDE.md           ← 项目专属指引
.goo/               ← 自动生成的执行记录
```

## 要求

- Claude Code
- 工具权限：Read, Write, Edit, Bash, WebSearch, Agent
- （可选）Goo-wiki Obsidian vault 用于归档
