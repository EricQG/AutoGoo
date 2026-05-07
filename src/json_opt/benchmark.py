"""JSON 序列化基准测试框架。

提供统一的评测接口，支持多次运行取平均，记录耗时、内存、输出大小。
"""

import time
import tracemalloc
from typing import Any, Callable, Protocol


class BenchmarkResult:
    """一次 benchmark 运行的结果。"""

    def __init__(self, name: str):
        self.name = name
        self.serialize_time_ms: float = 0.0
        self.deserialize_time_ms: float = 0.0
        self.memory_peak_mb: float = 0.0
        self.output_size_bytes: int = 0
        self.num_records: int = 0

    def __repr__(self) -> str:
        return (
            f"{self.name}: "
            f"serialize={self.serialize_time_ms:.2f}ms, "
            f"deserialize={self.deserialize_time_ms:.2f}ms, "
            f"memory={self.memory_peak_mb:.2f}MB, "
            f"output={self.output_size_bytes / 1024:.1f}KB"
        )


class Serializer(Protocol):
    """序列化器接口。所有实现必须符合此协议。"""

    def serialize(self, data: Any) -> bytes: ...

    def deserialize(self, data: bytes) -> Any: ...

    @property
    def name(self) -> str: ...


def run_benchmark(
    serializer: Serializer,
    data: Any,
    num_runs: int = 3,
    label: str | None = None,
) -> BenchmarkResult:
    """对给定的序列化器运行基准测试。

    参数:
        serializer: 实现了 Serializer 协议的对象
        data: 要序列化的数据
        num_runs: 运行次数（取平均）
        label: 结果标签（默认使用 serializer.name）

    返回:
        BenchmarkResult 对象
    """
    result = BenchmarkResult(label or serializer.name)

    # 获取数据大小
    if isinstance(data, list):
        result.num_records = len(data)
    elif isinstance(data, dict):
        result.num_records = len(data)
    else:
        result.num_records = 1

    # ---- 预热 ----
    _ = serializer.serialize(data)

    # ---- 序列化测试（不包含 tracemalloc，避免 overhead 污染计时） ----
    serialize_times: list[float] = []
    output: bytes = b""

    for _ in range(num_runs):
        start = time.perf_counter()
        output = serializer.serialize(data)
        elapsed = time.perf_counter() - start
        serialize_times.append(elapsed * 1000)  # 转为 ms

    result.serialize_time_ms = sum(serialize_times) / len(serialize_times)
    result.output_size_bytes = len(output)

    # ---- 内存测试（单独跑，使用 tracemalloc） ----
    tracemalloc.start()
    _ = serializer.serialize(data)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    result.memory_peak_mb = peak / (1024 * 1024)

    # ---- 反序列化测试 ----
    deserialize_times: list[float] = []
    for _ in range(num_runs):
        start = time.perf_counter()
        _ = serializer.deserialize(output)
        elapsed = time.perf_counter() - start
        deserialize_times.append(elapsed * 1000)

    result.deserialize_time_ms = sum(deserialize_times) / len(deserialize_times)

    return result


def print_comparison(results: list[BenchmarkResult]):
    """打印多个 BenchmarkResult 的对比表。"""
    if not results:
        return

    print(f"\n{'='*80}")
    print(f"{'JSON 序列化 Benchmark 对比':^80}")
    print(f"{'='*80}")
    print(f"{'实现':<20} {'序列化(ms)':<15} {'反序列化(ms)':<15} {'内存(MB)':<12} {'输出(KB)':<12} {'记录数':<10}")
    print(f"{'-'*80}")

    for r in results:
        print(
            f"{r.name:<20} {r.serialize_time_ms:<15.2f} {r.deserialize_time_ms:<15.2f} "
            f"{r.memory_peak_mb:<12.2f} {r.output_size_bytes / 1024:<12.1f} {r.num_records:<10}"
        )

    # 计算相对于第一个（baseline）的提升
    if len(results) >= 2:
        baseline = results[0]
        print(f"\n{'提升幅度（vs Baseline）':^80}")
        print(f"{'-'*80}")
        for r in results[1:]:
            ser_change = ((baseline.serialize_time_ms - r.serialize_time_ms) / baseline.serialize_time_ms) * 100
            deser_change = ((baseline.deserialize_time_ms - r.deserialize_time_ms) / baseline.deserialize_time_ms) * 100
            mem_change = ((baseline.memory_peak_mb - r.memory_peak_mb) / baseline.memory_peak_mb) * 100
            print(
                f"{r.name:<20} "
                f"序列化: {'+' if ser_change >= 0 else ''}{ser_change:+.1f}%  "
                f"反序列化: {'+' if deser_change >= 0 else ''}{deser_change:+.1f}%  "
                f"内存: {'+' if mem_change >= 0 else ''}{mem_change:+.1f}%"
            )
    print(f"{'='*80}\n")
