#!/usr/bin/env python3
"""Render a compact AutoGoo status dashboard from .goo/plan.json."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def bar(percent: int, width: int = 20) -> str:
    percent = max(0, min(100, percent))
    filled = round(width * percent / 100)
    return "█" * filled + "░" * (width - filled)


def output_preview(output: str | None) -> str:
    if not output:
        return "..."
    first = output.split(",")[0].strip()
    path = Path(first)
    if path.exists() and path.is_file():
        try:
            lines = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))
            return f"{lines}行"
        except OSError:
            return "存在"
    return "..."


def dep_names(step: dict[str, Any], steps_by_id: dict[int, dict[str, Any]]) -> str:
    missing = []
    for dep in step.get("depends_on", []):
        dep_step = steps_by_id.get(dep)
        if not dep_step or dep_step.get("status") != "completed":
            missing.append(dep_step.get("name", str(dep)) if dep_step else str(dep))
    if not missing:
        return "就绪"
    if len(missing) > 2:
        return "等待 " + " ".join(missing[:2]) + f" +{len(missing) - 2}"
    return "等待 " + " ".join(missing)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AutoGoo status")
    parser.add_argument("--plan", default=".goo/plan.json", help="plan.json path")
    args = parser.parse_args()

    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise SystemExit(f"plan not found: {plan_path}")

    data = json.loads(plan_path.read_text(encoding="utf-8"))
    steps = data.get("steps", [])
    steps_by_id = {step.get("id"): step for step in steps if isinstance(step.get("id"), int)}
    now = datetime.now(timezone.utc)

    total = len(steps)
    completed = sum(1 for s in steps if s.get("status") == "completed")
    avg = round(sum(int(s.get("progress", 100 if s.get("status") == "completed" else 0) or 0) for s in steps) / total) if total else 0
    task = data.get("task", "AutoGoo")

    print("═" * 62)
    print(f"  {task}  {completed}/{total}  {bar(avg)}  {avg}%")
    print("═" * 62)

    running = [s for s in steps if s.get("status") == "running"]
    if running:
        print("\n▶ 执行中")
        for step in running:
            progress = int(step.get("progress", 0) or 0)
            hb = parse_time(step.get("heartbeat_at"))
            age = ""
            if hb:
                mins = int((now - hb).total_seconds() // 60)
                age = f"  心跳 {mins}min前"
            print(f"  {step.get('name')}  {bar(progress, 16)}  {progress:>3}%  {output_preview(step.get('output'))}{age}")

    pending = [s for s in steps if s.get("status", "pending") == "pending"]
    if pending:
        print("\n⏳ 待执行")
        for step in pending:
            print(f"  {step.get('name')}  {dep_names(step, steps_by_id)}")

    done = [s for s in steps if s.get("status") == "completed"]
    if done:
        print("\n✅ 已完成")
        chunks = [f"{s.get('name')} {output_preview(s.get('output'))}" for s in done[:8]]
        suffix = f" · ... 等 {len(done) - 8} 步" if len(done) > 8 else ""
        print("  " + " · ".join(chunks) + suffix)

    warnings = []
    for step in steps:
        if step.get("status") == "failed":
            warnings.append(f"{step.get('name')} 失败: {step.get('error', '见日志')}")
        if step.get("status") == "running":
            hb = parse_time(step.get("heartbeat_at"))
            if not hb:
                warnings.append(f"{step.get('name')} running 但没有 heartbeat_at")
            elif (now - hb).total_seconds() >= 120:
                mins = int((now - hb).total_seconds() // 60)
                warnings.append(f"{step.get('name')} 无心跳 {mins}min，可能已停止")
    if warnings:
        print("\n⚠ 告警")
        for item in warnings:
            print(f"  {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
