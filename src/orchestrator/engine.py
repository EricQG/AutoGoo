"""执行引擎 — 按调度计划驱动步骤执行。"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


LOGS_DIR = Path(".goo/logs")


@runtime_checkable
class TaskStep(Protocol):
    """所有可执行步骤必须实现的接口。"""

    id: int
    name: str
    type: str  # "exec" | "optimize" | "eval"

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """执行步骤，返回结果。

        返回格式: {"status": "ok"|"failed", "output": ..., "metrics": {...}}
        """
        ...


class StepResult:
    """单步执行结果。"""

    def __init__(
        self,
        step_id: int,
        step_name: str,
        status: str,
        output: Any = None,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
        elapsed_s: float = 0.0,
    ) -> None:
        self.step_id = step_id
        self.step_name = step_name
        self.status = status
        self.output = output
        self.metrics = metrics or {}
        self.error = error
        self.elapsed_s = elapsed_s

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status,
            "output": self.output,
            "metrics": self.metrics,
            "error": self.error,
            "elapsed_s": self.elapsed_s,
        }


class Engine:
    """执行引擎。接收 plan.json → 按轮次执行 → 结果合并。"""

    def __init__(self, plan: dict[str, Any]) -> None:
        self.plan = plan
        self.results: dict[int, StepResult] = {}

    async def run_round(self, steps: list[dict[str, Any]], context: dict[str, Any]) -> list[StepResult]:
        """执行一轮中的多个步骤（当前为串行，后续可改为并行）。"""
        round_results: list[StepResult] = []

        for step_def in steps:
            t0 = time.time()
            try:
                # 检查是否有已注册的 handler
                output = {"step_id": step_def["id"], "name": step_def["name"]}
                status = "ok"
                error = None
            except Exception as e:
                output = None
                status = "failed"
                error = str(e)

            elapsed = time.time() - t0
            result = StepResult(
                step_id=step_def["id"],
                step_name=step_def["name"],
                status=status,
                output=output,
                elapsed_s=elapsed,
                error=error,
            )
            round_results.append(result)
            self.results[step_def["id"]] = result

        return round_results

    def get_context_for(self, step: dict[str, Any]) -> dict[str, Any]:
        """收集上游步骤的输出作为上下文。"""
        deps = step.get("depends_on", [])
        context: dict[str, Any] = {"upstream": {}}

        for dep_id in deps:
            if dep_id in self.results:
                context["upstream"][str(dep_id)] = self.results[dep_id].to_dict()

        return context

    def write_log(self, step: dict[str, Any], result: StepResult) -> Path:
        """将单步结果写入 .goo/logs/。"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        log_path = LOGS_DIR / f"{timestamp}_step-{step['id']}_{step['name']}.md"

        content = (
            f"# Step {step['id']}: {step['name']}\n\n"
            f"| 字段 | 值 |\n"
            f"|------|-----|\n"
            f"| **ID** | {step['id']} |\n"
            f"| **时间** | {timestamp} |\n"
            f"| **状态** | {'✅ Completed' if result.status == 'ok' else '❌ Failed'} |\n"
            f"| **耗时** | {result.elapsed_s:.2f}s |\n\n"
        )

        if result.error:
            content += f"## 错误\n\n{result.error}\n\n"

        log_path.write_text(content, encoding="utf-8")
        return log_path

    def summary(self) -> str:
        """生成执行汇总。"""
        lines = ["# 执行汇总\n", f"**任务**: {self.plan.get('task', '')}\n\n"]
        lines.append("| Step | 名称 | 状态 | 耗时 |\n")
        lines.append("|------|------|------|------|\n")

        for sid in sorted(self.results):
            r = self.results[sid]
            status_icon = "✅" if r.status == "ok" else "❌"
            lines.append(f"| {r.step_id} | {r.step_name} | {status_icon} | {r.elapsed_s:.2f}s |\n")

        total = sum(r.elapsed_s for r in self.results.values())
        lines.append(f"\n**总体耗时**: {total:.2f}s\n")
        return "".join(lines)
