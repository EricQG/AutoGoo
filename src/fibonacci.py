"""斐波那契数列 — 递归 vs 迭代性能对比。"""

import time
from functools import lru_cache


def fib_recursive(n: int) -> int:
    if n < 2:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)


@lru_cache(maxsize=None)
def fib_cached(n: int) -> int:
    if n < 2:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)


def fib_iterative(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def benchmark(n: int = 35) -> None:
    print(f"Fibonacci({n}) 性能对比\n")

    # 朴素递归（n 不能太大，否则太慢）
    t0 = time.perf_counter()
    r1 = fib_recursive(n)
    t1 = time.perf_counter()
    print(f"  递归:        {n} → {r1}, {t1-t0:.4f}s")

    # 缓存递归
    t0 = time.perf_counter()
    r2 = fib_cached(n)
    t1 = time.perf_counter()
    print(f"  缓存递归:    {n} → {r2}, {t1-t0:.4f}s")

    # 迭代
    t0 = time.perf_counter()
    r3 = fib_iterative(n)
    t1 = time.perf_counter()
    print(f"  迭代:        {n} → {r3}, {t1-t0:.4f}s")

    # 大数测试迭代性能
    for big_n in [100, 1000, 10_000]:
        t0 = time.perf_counter()
        r = fib_iterative(big_n)
        t1 = time.perf_counter()
        print(f"  迭代(n={big_n}): {t1-t0:.6f}s (结果 {len(str(r))} 位)")
    print()


if __name__ == "__main__":
    benchmark()
