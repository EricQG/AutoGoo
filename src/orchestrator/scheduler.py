"""DAG 调度器 — 按 depends_on 推导执行轮次和并行关系。"""

from __future__ import annotations

from typing import Any


class StepDef:
    """任务步骤定义。对应 plan.json 中的一个 step。"""

    def __init__(self, id: int, name: str, depends_on: list[int], type: str, description: str = "") -> None:
        self.id = id
        self.name = name
        self.description = description
        self.depends_on = depends_on
        self.type = type  # "exec" | "optimize" | "eval"

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StepDef:
        return cls(
            id=d["id"],
            name=d["name"],
            depends_on=d.get("depends_on", []),
            type=d.get("type", "exec"),
            description=d.get("description", ""),
        )

    def __repr__(self) -> str:
        return f"StepDef({self.id}, {self.name!r}, depends_on={self.depends_on})"


class RoundGroup:
    """同一轮次中可并行执行的一组步骤。"""

    def __init__(self, round_num: int, steps: list[StepDef]) -> None:
        self.round_num = round_num
        self.steps = steps

    def __repr__(self) -> str:
        return f"RoundGroup({self.round_num}, steps={[s.id for s in self.steps]})"


def build_schedule(steps: list[StepDef]) -> list[RoundGroup]:
    """按 depends_on 拓扑排序，返回按轮次分组的执行计划。

    算法：
    1. 找出所有 depends_on 为空的步骤 → 第一轮
    2. 移除第一轮步骤，找出新的 depends_on 为空的 → 第二轮
    3. 重复直到所有步骤执行完毕
    4. 同一轮的步骤可并行执行
    """
    remaining = {s.id: s for s in steps}
    executed: set[int] = set()
    rounds: list[RoundGroup] = []
    round_num = 0

    while remaining:
        round_num += 1
        # 本轮可执行的步骤：所有依赖都已执行
        current = [
            s
            for s in remaining.values()
            if all(dep in executed for dep in s.depends_on)
        ]

        if not current:
            # 存在循环依赖或孤立依赖
            unexecuted = [s.id for s in remaining.values()]
            raise ValueError(
                f"Cannot schedule: steps {unexecuted} have unsatisfied dependencies. "
                f"Check for circular or missing dependencies."
            )

        rounds.append(RoundGroup(round_num, current))

        for s in current:
            executed.add(s.id)
            del remaining[s.id]

    return rounds


def schedule_from_plan(plan: dict[str, Any]) -> list[RoundGroup]:
    """从 plan.json 字典直接生成调度计划。"""
    steps = [StepDef.from_dict(s) for s in plan["steps"]]
    return build_schedule(steps)


def validate_dag(steps: list[StepDef]) -> list[str]:
    """验证 DAG 合法性，返回警告列表。"""
    warnings: list[str] = []
    step_ids = {s.id for s in steps}

    for s in steps:
        for dep in s.depends_on:
            if dep not in step_ids:
                warnings.append(
                    f"Step {s.id} ({s.name}) depends on non-existent step {dep}"
                )

    return warnings
