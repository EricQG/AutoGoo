---
name: auto-goo
description: AutoGoo 自动化工作流。当用户下达可分解的多步任务时触发。完整实现位于 auto-goo plugin（project-root/plugin/），提供任务解析 → DAG 执行 → 优化 → 归档的完整流程。
---

# AutoGoo

AutoGoo 工作流定义在本仓库的 `skills/auto-goo/` 中。

使用方式（本仓库即插件）：
```
cc --plugin git+https://github.com/ZixiGu/AutoGoo.git
```

核心规范文件：
- `skills/auto-goo/SKILL.md` — 工作流入口
- `skills/auto-goo/references/` — 各阶段详细规范
