---
name: auto-goo:goo-benchmark
description: 启动性能评测与优化迭代 — 搜索指标、基线评测、瓶颈分析、优化对比
---

# /auto-goo:goo-benchmark — 启动优化迭代

对当前任务或指定功能执行性能评测与优化迭代。

## 执行流程

1. WebSearch 搜索该领域标准评价指标
2. 实现基线版本并评测（至少 3 次取平均）
3. 瓶颈分析（cProfile / py-spy / tracemalloc / 大 O 推算）
4. 优化 → 同指标评测对比
5. 终止判断：提升 < 20% 或连续两轮 < 5% 停止

## 示例

```
/auto-goo:goo-benchmark
优化
评测
```

## 备注

- 默认最多 3 轮优化迭代
- 计时与内存测量分开进行
- 详见 `skills/auto-goo/references/optimization-loop.md`
