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
TIMESTAMP=$(date +"%Y-%m-%dT%H-%M-%S")
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
PLAN_FILE="$PROJECT_ROOT/.goo/plan.json"
PLAN_HISTORY_DIR="$PROJECT_ROOT/.goo/plans/history"

mkdir -p "$PROJECT_ROOT/.goo"

if [ -f "$PLAN_FILE" ]; then
  mkdir -p "$PLAN_HISTORY_DIR"
  ARCHIVE_TIMESTAMP=$(date +"%Y-%m-%dT%H-%M-%S")
  ARCHIVE_FILE="$PLAN_HISTORY_DIR/plan-$ARCHIVE_TIMESTAMP.json"
  ARCHIVE_INDEX=1
  while [ -e "$ARCHIVE_FILE" ]; do
    ARCHIVE_FILE="$PLAN_HISTORY_DIR/plan-$ARCHIVE_TIMESTAMP-$ARCHIVE_INDEX.json"
    ARCHIVE_INDEX=$((ARCHIVE_INDEX + 1))
  done
  cp "$PLAN_FILE" "$ARCHIVE_FILE"
  echo "✓ previous plan archived at $ARCHIVE_FILE"
fi

# Build steps JSON. AutoGoo plans always end with a wiki archive step by
# default, so goo-start/goo-continue can preserve lessons after execution.
STEPS=""
for i in $(seq 1 "$COUNT"); do
  if [ "$i" -eq 1 ]; then
    DEPS="[]"
  else
    DEPS="[$((i-1))]"
  fi
  STEP="    { \"id\": $i, \"tier\": 1, \"name\": \"步骤$i\", \"description\": \"步骤$i 描述\", \"depends_on\": $DEPS, \"type\": \"exec\", \"subagent\": \"implementer\" }"
  if [ -z "$STEPS" ]; then
    STEPS="$STEP"
  else
    STEPS="$STEPS,
$STEP"
  fi
done

ARCHIVE_ID=$((COUNT + 1))
ARCHIVE_TIER=$((COUNT + 1))
ARCHIVE_DEPS="[$COUNT]"
ARCHIVE_STEP="    { \"id\": $ARCHIVE_ID, \"tier\": $ARCHIVE_TIER, \"name\": \"归档到 Goo-wiki\", \"description\": \"将任务目标、计划、关键证据、产物路径、验证结果、决策和可复用经验归档到 Goo-wiki；维护任务页、项目入口、相关概念/问题/指标页和 log.md 的 Wikilink；Goo-wiki 不可用时写入 .goo/obsidian/ fallback\", \"depends_on\": $ARCHIVE_DEPS, \"type\": \"archive\", \"subagent\": \"recorder\" }"
STEPS="$STEPS,
$ARCHIVE_STEP"

cat > "$PLAN_FILE" << EOF
{
  "task": "$TASK",
  "status": "pending",
  "created_at": "$TIMESTAMP",
  "started_at": null,
  "completed_at": null,
  "wiki_context": {
    "found": false,
    "sources": [],
    "reused_knowledge": []
  },
  "context_digest": {
    "found": false,
    "decisions": [],
    "constraints": [],
    "acceptance_criteria": [],
    "open_questions": []
  },
  "context_artifacts": [],
  "steps": [
$STEPS
  ]
}
EOF

echo "✓ plan.json created at $PLAN_FILE ($COUNT steps + wiki archive)"
