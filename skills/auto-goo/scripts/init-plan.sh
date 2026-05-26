#!/bin/bash
# AutoGoo: 初始化 plan.json 模板
# Usage: ./scripts/init-plan.sh "<task_description>" [step_count]
#   step_count: 非归档步骤数量，默认 1；脚本会自动追加最后的 Wiki 归档步骤

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"<task_description>\" [step_count]"
  echo "  step_count: number of non-archive steps (default: 1)"
  exit 1
fi

TASK="$1"
COUNT="${2:-1}"

python3 - "$TASK" "$COUNT" <<'PY'
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def project_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        root = result.stdout.strip()
        if root:
            return Path(root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return Path.cwd()


def archive_existing_plan(plan_file: Path, history_dir: Path) -> Path | None:
    if not plan_file.exists():
        return None
    history_dir.mkdir(parents=True, exist_ok=True)
    base = history_dir / f"plan-{timestamp()}.json"
    archive_file = base
    index = 1
    while archive_file.exists():
        archive_file = history_dir / f"{base.stem}-{index}.json"
        index += 1
    shutil.copy2(plan_file, archive_file)
    return archive_file


def make_step(step_id: int) -> dict[str, Any]:
    output = f".goo/artifacts/step-{step_id}-output.md"
    return {
        "id": step_id,
        "goal_id": "g1",
        "tier": 1,
        "name": f"步骤{step_id}",
        "description": (
            f"步骤{step_id} 描述。请在执行前把本步骤改写为自包含描述，"
            "包含输入、边界、输出和验收点。"
        ),
        "depends_on": [],
        "type": "exec",
        "subagent": "implementer",
        "status": "pending",
        "progress": 0,
        "output": output,
        "inputs": [],
        "outputs": [output],
        "allowed_read_paths": ["."],
        "allowed_write_paths": [".goo/artifacts/"],
        "validation": "产物存在且满足本步骤描述中的验收点",
        "risk_level": "low",
        "requires_user_confirm": False,
        "agent_id": None,
        "heartbeat_at": None,
        "started_at": None,
        "completed_at": None,
    }


def main() -> int:
    task = sys.argv[1]
    try:
        count = int(sys.argv[2])
    except ValueError as exc:
        raise SystemExit(f"step_count must be an integer: {sys.argv[2]}") from exc
    if count < 1:
        raise SystemExit("step_count must be >= 1")

    root = project_root()
    goo_dir = root / ".goo"
    plan_file = goo_dir / "plan.json"
    history_dir = goo_dir / "plans" / "history"
    goo_dir.mkdir(parents=True, exist_ok=True)

    archived = archive_existing_plan(plan_file, history_dir)
    if archived:
        print(f"✓ previous plan archived at {archived}")

    steps = [make_step(i) for i in range(1, count + 1)]
    archive_id = count + 1
    archive_output = ".goo/obsidian/<project-slug>/"
    steps.append(
        {
            "id": archive_id,
            "goal_ids": ["g1"],
            "tier": 2,
            "name": "归档到 Goo-wiki",
            "description": (
                "将任务目标、计划、关键证据、产物路径、验证结果、决策和可复用经验"
                "归档到 Goo-wiki；必须补齐任务页、项目入口 index.md、log.md、复用知识页"
                "和新增经验页之间的 Wikilink/backlink 关系，防止 Obsidian 连接图谱断裂；"
                "Goo-wiki 不可用时写入 .goo/obsidian/ fallback"
            ),
            "depends_on": [step["id"] for step in steps],
            "type": "archive",
            "subagent": "recorder",
            "status": "pending",
            "progress": 0,
            "output": archive_output,
            "inputs": [step["output"] for step in steps],
            "outputs": [archive_output],
            "allowed_read_paths": [".goo/plan.json", ".goo/logs/", ".goo/artifacts/"],
            "allowed_write_paths": [".goo/obsidian/"],
            "validation": (
                "归档页或 fallback 笔记存在；任务页链接项目入口、复用的 wiki_context/context_artifacts "
                "和关键概念/问题/指标/历史任务页；项目 index.md 与 log.md 反向链接任务页；"
                "新增 concept/lessons/metrics 页也链接回任务页或项目入口；记录产物路径、验证结果和可复用经验"
            ),
            "risk_level": "low",
            "requires_user_confirm": False,
            "agent_id": None,
            "heartbeat_at": None,
            "started_at": None,
            "completed_at": None,
        }
    )

    plan = {
        "task": task,
        "goals": [
            {
                "id": "g1",
                "name": task,
                "description": "默认目标。若任务包含多个交付目标，goo-plan 应改写为多个 goals 并为步骤绑定 goal_id 或 goal_ids。",
                "priority": 1,
                "status": "pending",
                "acceptance_criteria": [],
                "outputs": [],
                "depends_on": [],
            }
        ],
        "status": "pending",
        "created_at": timestamp(),
        "started_at": None,
        "completed_at": None,
        "max_concurrent": 6,
        "wiki_context": {
            "found": False,
            "sources": [],
            "reused_knowledge": [],
        },
        "context_digest": {
            "found": False,
            "decisions": [],
            "constraints": [],
            "acceptance_criteria": [],
            "open_questions": [],
            "post_plan_updates": [],
        },
        "context_artifacts": [],
        "steps": steps,
    }

    plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"✓ plan.json created at {plan_file} ({count} steps + wiki archive)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
PY
