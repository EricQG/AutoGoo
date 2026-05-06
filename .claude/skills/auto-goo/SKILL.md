---
name: auto-goo
description: 启动 AutoGoo 自动化工作流。收到任务后自动解析步骤 → 并行/串行执行 → 优化迭代 → 归档到 Goo-wiki。遵循 CLAUDE.md 定义的全部规范。
tools: Read, Write, Edit, Bash, WebSearch, Agent
---

# AutoGoo 自动化工作流

当用户说"开始任务"、"/auto-goo"或下达一个可分解的任务时，启动此工作流。

## 工作流

### Phase 1: 任务解析

1. 读取 `CLAUDE.md` 确认当前规范（项目定位、核心原则、Quick Start）
2. 按 1.1 解析流程拆解任务：
   - 识别最终交付物
   - 逆向拆解为原子步骤
   - 标注依赖关系
   - 识别优化标记
3. 输出 `.goo/plan.json`（遵循 1.3 格式）

### Phase 2: 执行

按 2.1 执行流程逐轮执行：
- 同一轮无依赖步骤 → **必须并行分发** (Agent with `run_in_background: true`)
- 每步完成后写入 `.goo/logs/`（按 4.2 模板）
- 失败按 2.3 错误处理

### Phase 3: 优化迭代

当步骤标记为 `type: "optimize"` 时，启动 3.1 优化循环：
1. WebSearch / context7 搜索评价指标
2. Baseline 实现与评测
3. 瓶颈分析
4. 优化 → 评测 → 对比
5. 按 3.4 终止条件决定是否继续

### Phase 4: Obsidian 归档

每步完成 + 全部完成后，启动 Recorder 流程（2.5.7）：
- 写入 `Goo-wiki/wiki/projects/<slug>/` 或 fallback `.goo/obsidian/`
- 遵循 Goo-wiki 规范（frontmatter、wikilink、tag: auto-goo）
- 追加 `Goo-wiki/log.md`

## 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| task | 任务描述（必填） | "实现一个高性能 CSV 解析器" |
| project | 项目领域（可选，默认 auto-infer） | "csv-parser" |

## 示例

```
用户: /auto-goo 用 Python 写一个快速排序，并优化性能
→ 解析: 实现baseline + 优化(并行为2步) + 评测
→ 执行: 并行分发 baseline 和优化实现
→ 优化: 搜索排序 benchmark 指标 → profile → 优化 → 对比
→ 归档: 写入 Goo-wiki/wiki/projects/sort-algo/
```
