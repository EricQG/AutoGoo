"""Profiling 工具 — 分析 JSON 序列化瓶颈。"""

import cProfile
import pstats
import io
import time
from typing import Any

from .test_data import generate_orders
from .baseline import BaselineSerializer


def profile_serialize(data: list[dict[str, Any]] | None = None, num_records: int = 5000):
    """对基线序列化器做 CPU profiling。

    使用 cProfile 分析序列化过程中的热点函数。
    """
    if data is None:
        data = generate_orders(num_records)

    serializer = BaselineSerializer()

    profiler = cProfile.Profile()
    profiler.enable()

    for _ in range(3):
        _ = serializer.serialize(data)

    profiler.disable()

    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumtime")
    ps.print_stats(20)

    print("=" * 60)
    print("cProfile 结果 (top 20 by cumulative time)")
    print("=" * 60)
    print(s.getvalue())

    # 用简易计时分析各环节
    print("=" * 60)
    print("分段计时分析")
    print("=" * 60)

    # 测试各种 json.dumps 参数的影响
    for kwargs, label in [
        ({"ensure_ascii": True, "sort_keys": False}, "ensure_ascii=True"),
        ({"ensure_ascii": False, "sort_keys": False}, "ensure_ascii=False"),
        ({"ensure_ascii": True, "sort_keys": True}, "sort_keys=True"),
        ({"ensure_ascii": False, "sort_keys": True}, "both"),
    ]:
        import json
        times = []
        for _ in range(3):
            start = time.perf_counter()
            json.dumps(data, **kwargs)
            times.append((time.perf_counter() - start) * 1000)
        avg = sum(times) / len(times)
        print(f"  {label:<30s}: {avg:.2f}ms")


def profile_memory(data: list[dict[str, Any]] | None = None, num_records: int = 10000):
    """分析序列化的内存分配模式。"""
    if data is None:
        data = generate_orders(num_records)

    import tracemalloc

    serializer = BaselineSerializer()

    # 快照基线
    tracemalloc.start()

    # 多次序列化
    for _ in range(5):
        _ = serializer.serialize(data)

    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()

    top_stats = snapshot.statistics("lineno")

    print("=" * 60)
    print("内存分配热点 (top 10)")
    print("=" * 60)
    for stat in top_stats[:10]:
        print(stat)

    print(f"\n共 {sum(stat.size for stat in top_stats)} 字节分配")


if __name__ == "__main__":
    profile_serialize()
    print()
    profile_memory()
