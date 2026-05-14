# AutoGoo — 自动化智能体编排框架

## 项目定位

AutoGoo 是一个自动化智能体编排框架。接收用户任务后自动解析为执行步骤，按依赖关系并行或串行执行，遇到性能优化场景自动迭代，并自动搜索评价指标用于评测。每一步执行都必须留下结构化记录。

**核心原则**：
- **先解析，再执行** — 绝不直接动手，先规划成 DAG
- **能并行就不串行** — 无依赖的步骤必须并行分发
- **优化必有指标** — 没有量化指标就不算优化
- **执行必留痕** — 每一步都归档到 `.goo/logs/`
- **rm 必问许可** — 删除项目目录外的文件/目录前必须先问用户，取得明确确认后才能执行

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

完整工作流定义在 **goo-workflow skill** 中，快捷命令表也见该文件：

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

AutoGoo 插件自身应当根据实际使用持续迭代。每次执行都是收集改进信号的素材。

### 触发方式

| 时机 | 方式 | 动作 |
|------|------|------|
| 每次任务后 | 自动记录 | 在日志末尾追加 `## 流程问题` 反思 |
| 每 5 个任务 | `/auto-goo:goo-improve` 流程 | 汇总高频问题，生成修改方案 |
| 用户主动 | `/auto-goo:goo-improve` 或 `优化AutoGoo` | 立即启动改进分析 |

### 问题记录格式

在 `.goo/logs/` 的任务日志末尾追加结构化反思：

```yaml
## 流程问题
- 问题: "<具体问题>"
  根因: "<根因分析>"
  改进: "<建议修改的文件和内容>"
  优先级: high | medium | low
```

### 修改决策

| 信号 | 改什么 |
|------|--------|
| 命令弹窗频繁 | `settings.local.json` allowlist |
| 解析遗漏 | `references/task-parsing.md` |
| 流程指引不足 | `references/execution-engine.md` |
| 技能触发不准 | `SKILL.md` description |

完整自改进规范 → `skills/auto-goo/references/self-improvement.md`
