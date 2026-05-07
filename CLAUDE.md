# AutoGoo — 自动化智能体编排框架

## 项目定位

AutoGoo 是一个自动化智能体编排框架。接收用户任务后自动解析为执行步骤，按依赖关系并行或串行执行，遇到性能优化场景自动迭代，并自动搜索评价指标用于评测。每一步执行都必须留下结构化记录。

**核心原则**：
- **先解析，再执行** — 绝不直接动手，先规划成 DAG
- **能并行就不串行** — 无依赖的步骤必须并行分发
- **优化必有指标** — 没有量化指标就不算优化
- **执行必留痕** — 每一步都归档到 `.goo/logs/`

## 快速开始 (Quick Start)

每次会话加载后，按以下顺序行动：

```
1. Goo-wiki vault 检测
   → SessionStart hook 自动执行（配置见 skills/auto-goo/references/setup.md）
   → vault 不存在则使用 .goo/obsidian/ fallback

2. 检查未完成任务
   → SessionStart hook 读取 .goo/plan.json（如果存在）
   → 有未完成步骤则询问用户是否继续

3. 等待用户下达任务
```

## 核心工作流

完整工作流定义在 **auto-goo skill** 中，快捷命令表也见该文件：

```
skills/auto-goo/SKILL.md
```

各阶段详细规范：
- **环境设置** — `skills/auto-goo/references/setup.md`
- **任务解析** — `skills/auto-goo/references/task-parsing.md`
- **执行引擎** — `skills/auto-goo/references/execution-engine.md`
- **优化循环** — `skills/auto-goo/references/optimization-loop.md`
- **Obsidian 归档** — `skills/auto-goo/references/obsidian-archive.md`
- **Python 规范** — `skills/auto-goo/references/python-standards.md`

## 流程自省与持续改进

每次执行过程中遇到的摩擦、歧义、缺失都应当被记录。

### 问题记录格式

在任务日志的末尾追加 `## 流程问题` 小节：

```markdown
## 流程问题
1. <问题描述> — <建议改进方向>
```

### 定期回顾

每执行 3-5 个任务后回顾问题记录。高频问题更新到 plugin 的 references/ 中。
