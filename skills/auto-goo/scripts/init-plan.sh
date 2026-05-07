#!/bin/bash
# AutoGoo: 初始化 plan.json 模板
# Usage: ./scripts/init-plan.sh "<task_description>" [step_count]
#   step_count: 步骤数量，默认 1

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"<task_description>\" [step_count]"
  echo "  step_count: number of steps (default: 1)"
  exit 1
fi

TASK="$1"
COUNT="${2:-1}"
TIMESTAMP=$(date +"%Y-%m-%dT%H-%M-%S")
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

mkdir -p "$PROJECT_ROOT/.goo"

# Build steps JSON
STEPS=""
for i in $(seq 1 "$COUNT"); do
  if [ "$i" -eq 1 ]; then
    DEPS="[]"
  else
    DEPS="[$((i-1))]"
  fi
  STEP="    { \"id\": $i, \"tier\": 1, \"name\": \"步骤$i\", \"description\": \"步骤$i 描述\", \"depends_on\": $DEPS, \"type\": \"exec\" }"
  if [ -z "$STEPS" ]; then
    STEPS="$STEP"
  else
    STEPS="$STEPS,
$STEP"
  fi
done

cat > "$PROJECT_ROOT/.goo/plan.json" << EOF
{
  "task": "$TASK",
  "created_at": "$TIMESTAMP",
  "steps": [
$STEPS
  ]
}
EOF

echo "✓ plan.json created at $PROJECT_ROOT/.goo/plan.json ($COUNT steps)"
