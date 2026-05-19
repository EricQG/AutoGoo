#!/usr/bin/env bash
# AutoGoo: interactive configuration initializer
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  goo-init.sh [--user|--project] [--wiki-dir PATH] [--project-slug SLUG] [--yes] [--force] [--update-claude-md] [--skip-claude-md]

Options:
  --user            Write user-level config to ~/.auto-goo/config.json
  --project         Write project-level config to .goo/config.json
  --wiki-dir PATH   Set Goo-wiki directory (default: ~/workspace/Goo-wiki)
  --project-slug SLUG
                    Set Goo-wiki project archive folder name (default: project directory name)
  --yes             Use defaults for unanswered prompts
  --force           Overwrite existing config without asking
  --update-claude-md
                    Update project CLAUDE.md without asking
  --skip-claude-md  Do not update project CLAUDE.md when Goo-wiki is available
  -h, --help        Show this help
EOF
}

SCOPE=""
WIKI_DIR="${AUTO_GOO_WIKI_DIR:-}"
WIKI_DIR_PROVIDED=0
PROJECT_SLUG=""
YES=0
FORCE=0
UPDATE_CLAUDE_MD=0
SKIP_CLAUDE_MD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user)
      SCOPE="user"
      shift
      ;;
    --project)
      SCOPE="project"
      shift
      ;;
    --wiki-dir)
      if [[ $# -lt 2 ]]; then
        echo "error: --wiki-dir requires a path" >&2
        exit 2
      fi
      WIKI_DIR="$2"
      WIKI_DIR_PROVIDED=1
      shift 2
      ;;
    --project-slug)
      if [[ $# -lt 2 ]]; then
        echo "error: --project-slug requires a value" >&2
        exit 2
      fi
      PROJECT_SLUG="$2"
      shift 2
      ;;
    --yes|-y)
      YES=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --update-claude-md)
      UPDATE_CLAUDE_MD=1
      shift
      ;;
    --skip-claude-md)
      SKIP_CLAUDE_MD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$UPDATE_CLAUDE_MD" -eq 1 && "$SKIP_CLAUDE_MD" -eq 1 ]]; then
  echo "error: --update-claude-md and --skip-claude-md cannot be used together" >&2
  exit 2
fi

prompt() {
  local message="$1"
  local default_value="$2"
  local answer

  if [[ "$YES" -eq 1 || ! -t 0 ]]; then
    printf '%s\n' "$default_value"
    return
  fi

  read -r -p "$message [$default_value]: " answer
  if [[ -z "$answer" ]]; then
    printf '%s\n' "$default_value"
  else
    printf '%s\n' "$answer"
  fi
}

confirm() {
  local message="$1"
  local default_value="${2:-n}"
  local answer

  if [[ "$YES" -eq 1 || "$FORCE" -eq 1 || ! -t 0 ]]; then
    [[ "$default_value" == "y" ]]
    return
  fi

  read -r -p "$message [y/N]: " answer
  answer="${answer:-$default_value}"
  [[ "$answer" == "y" || "$answer" == "Y" || "$answer" == "yes" || "$answer" == "YES" ]]
}

expand_path() {
  local raw="$1"
  if [[ "$raw" == "~" ]]; then
    printf '%s\n' "$HOME"
  elif [[ "$raw" == "~/"* ]]; then
    printf '%s/%s\n' "$HOME" "${raw#\~/}"
  else
    printf '%s\n' "$raw"
  fi
}

project_root() {
  git rev-parse --show-toplevel 2>/dev/null || pwd
}

default_project_slug() {
  local root="$1"
  local raw
  raw="$(basename "$root")"
  raw="$(printf '%s\n' "$raw" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//; s/-+/-/g')"
  if [[ -z "$raw" ]]; then
    raw="project"
  fi
  printf '%s\n' "$raw"
}

git_remote_url() {
  local root="$1"
  local remote
  if ! git -C "$root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    return 1
  fi
  if git -C "$root" remote get-url origin 2>/dev/null; then
    return 0
  fi
  remote="$(git -C "$root" remote 2>/dev/null | sed -n '1p')"
  if [[ -n "$remote" ]]; then
    git -C "$root" remote get-url "$remote" 2>/dev/null
    return $?
  fi
  return 1
}

if [[ -z "$SCOPE" ]]; then
  if [[ ! -t 0 ]]; then
    echo "error: cannot choose init scope in non-interactive mode" >&2
    echo "hint: pass --user or --project explicitly" >&2
    exit 2
  fi
  SCOPE="$(prompt "Configure AutoGoo for user or project? (user/project)" "user")"
fi

case "$SCOPE" in
  user)
    CONFIG_DIR="$HOME/.auto-goo"
    CONFIG_FILE="$CONFIG_DIR/config.json"
    FALLBACK_DIR=".goo/obsidian"
    ;;
  project)
    ROOT="$(project_root)"
    CONFIG_DIR="$ROOT/.goo"
    CONFIG_FILE="$CONFIG_DIR/config.json"
    FALLBACK_DIR=".goo/obsidian"
    ;;
  *)
    echo "error: scope must be 'user' or 'project'" >&2
    exit 2
    ;;
esac

if [[ -z "$WIKI_DIR" ]]; then
  if [[ ! -t 0 ]]; then
    echo "error: cannot choose wiki_dir in non-interactive mode" >&2
    echo "hint: pass --wiki-dir ~/workspace/Goo-wiki or another Goo-wiki path explicitly" >&2
    exit 2
  fi
  DEFAULT_WIKI_DIR="$HOME/workspace/Goo-wiki"
  WIKI_DIR="$(prompt "Goo-wiki directory (press Enter to use default)" "$DEFAULT_WIKI_DIR")"
  WIKI_DIR_PROVIDED=1
elif [[ "$WIKI_DIR_PROVIDED" -eq 0 && -n "${AUTO_GOO_WIKI_DIR:-}" ]]; then
  WIKI_DIR_PROVIDED=1
fi

WIKI_DIR_EXPANDED="$(expand_path "$WIKI_DIR")"
WIKI_READY=0
PROJECT_ARCHIVE_DIR=""
FALLBACK_PROJECT_ARCHIVE_DIR=""
GIT_REMOTE_URL=""

if [[ "$SCOPE" == "project" ]]; then
  DEFAULT_PROJECT_SLUG="$(default_project_slug "$ROOT")"
  if [[ -z "$PROJECT_SLUG" ]]; then
    PROJECT_SLUG="$(prompt "Goo-wiki project archive slug" "$DEFAULT_PROJECT_SLUG")"
  fi
  PROJECT_SLUG="$(default_project_slug "$PROJECT_SLUG")"
  PROJECT_ARCHIVE_DIR="wiki/projects/$PROJECT_SLUG"
  FALLBACK_PROJECT_ARCHIVE_DIR="$FALLBACK_DIR/$PROJECT_SLUG"
  GIT_REMOTE_URL="$(git_remote_url "$ROOT" || true)"
fi

echo ""
echo "AutoGoo init"
echo "  scope:      $SCOPE"
echo "  config:     $CONFIG_FILE"
echo "  wiki_dir:   $WIKI_DIR"
if [[ "$SCOPE" == "project" ]]; then
  echo "  project:    $PROJECT_SLUG"
  if [[ -n "$GIT_REMOTE_URL" ]]; then
    echo "  git remote: $GIT_REMOTE_URL"
  fi
fi

if [[ -f "$WIKI_DIR_EXPANDED/CLAUDE.md" ]]; then
  WIKI_READY=1
  echo "  wiki check: ready ($WIKI_DIR_EXPANDED/CLAUDE.md)"
else
  echo "  wiki check: not found; archive will fall back to $FALLBACK_DIR"
fi

if [[ -f "$CONFIG_FILE" && "$FORCE" -ne 1 ]]; then
  echo ""
  echo "Existing config found:"
  sed -n '1,120p' "$CONFIG_FILE"
  echo ""
  if ! confirm "Overwrite $CONFIG_FILE?" "n"; then
    echo "Skipped. Existing config kept."
    exit 0
  fi
fi

if [[ "$SCOPE" == "project" && "$WIKI_READY" -eq 1 ]]; then
  mkdir -p "$WIKI_DIR_EXPANDED/$PROJECT_ARCHIVE_DIR"
  echo "  archive root: $WIKI_DIR_EXPANDED/$PROJECT_ARCHIVE_DIR"
  if [[ -n "$GIT_REMOTE_URL" ]]; then
    python3 - "$WIKI_DIR_EXPANDED/$PROJECT_ARCHIVE_DIR/index.md" "$PROJECT_SLUG" "$ROOT" "$GIT_REMOTE_URL" <<'PY'
import sys
from pathlib import Path

target = Path(sys.argv[1])
project_slug = sys.argv[2]
project_root = sys.argv[3]
git_remote_url = sys.argv[4]

begin = "<!-- AUTO-GOO-PROJECT-META-BEGIN -->"
end = "<!-- AUTO-GOO-PROJECT-META-END -->"
block = f"""{begin}
## Project Metadata

- Project slug: `{project_slug}`
- Local path: `{project_root}`
- Git repository: `{git_remote_url}`
{end}
"""

if target.exists():
    text = target.read_text(encoding="utf-8")
else:
    text = f"# {project_slug}\n"

if begin in text and end in text:
    prefix, rest = text.split(begin, 1)
    _, suffix = rest.split(end, 1)
    new_text = prefix.rstrip() + "\n\n" + block + suffix.lstrip("\n")
else:
    new_text = text.rstrip() + "\n\n" + block

target.write_text(new_text, encoding="utf-8")
PY
    echo "  project page: updated git repository in $WIKI_DIR_EXPANDED/$PROJECT_ARCHIVE_DIR/index.md"
  fi
fi

mkdir -p "$CONFIG_DIR"

python3 - "$CONFIG_FILE" "$WIKI_DIR" "$FALLBACK_DIR" "$PROJECT_SLUG" "$PROJECT_ARCHIVE_DIR" "$FALLBACK_PROJECT_ARCHIVE_DIR" "$GIT_REMOTE_URL" <<'PY'
import json
import sys
from pathlib import Path

target = Path(sys.argv[1])
wiki_dir = sys.argv[2]
fallback_dir = sys.argv[3]
project_slug = sys.argv[4]
project_archive_dir = sys.argv[5]
fallback_project_archive_dir = sys.argv[6]
git_remote_url = sys.argv[7]

config = {
    "version": 1,
    "wiki_dir": wiki_dir,
    "wiki": {
        "search_paths": [
            "wiki/projects",
            "wiki/concepts",
            "journal/weekly",
            "log.md",
        ],
    },
    "archive": {
        "enabled": True,
        "fallback_dir": fallback_dir,
        "plan_history_dir": ".goo/plans/history",
    },
    "execution": {
        "max_concurrent": 6,
        "heartbeat_seconds": 30,
        "stale_after_seconds": 120,
    },
    "planning": {
        "recall_wiki": True,
        "require_wiki_context": False,
    },
    "init": {
        "prompt_for_scope": True,
        "prompt_for_wiki_dir": True,
    },
}

if project_slug:
    config["archive"]["project_slug"] = project_slug
    config["archive"]["project_dir"] = project_archive_dir
    config["archive"]["fallback_project_dir"] = fallback_project_archive_dir
    if git_remote_url:
        config["archive"]["git_remote_url"] = git_remote_url

target.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

echo ""
echo "Wrote $CONFIG_FILE"

if [[ "$SCOPE" == "project" && "$WIKI_READY" -eq 1 && "$SKIP_CLAUDE_MD" -ne 1 ]]; then
  PROJECT_CLAUDE_MD="$ROOT/CLAUDE.md"
  SHOULD_UPDATE_CLAUDE_MD=0
  if [[ "$UPDATE_CLAUDE_MD" -eq 1 ]]; then
    SHOULD_UPDATE_CLAUDE_MD=1
  elif [[ "$YES" -eq 1 || ! -t 0 ]]; then
    echo "Project CLAUDE.md was not updated; rerun with --update-claude-md to add Goo-wiki archive principles."
  elif confirm "Add Goo-wiki archive principles to $PROJECT_CLAUDE_MD?" "y"; then
    SHOULD_UPDATE_CLAUDE_MD=1
  else
    echo "Skipped project CLAUDE.md update by user choice."
  fi

  if [[ "$SHOULD_UPDATE_CLAUDE_MD" -eq 1 ]]; then
    python3 - "$PROJECT_CLAUDE_MD" "$WIKI_DIR" "$FALLBACK_PROJECT_ARCHIVE_DIR" "$PROJECT_ARCHIVE_DIR" <<'PY'
import sys
from pathlib import Path

target = Path(sys.argv[1])
wiki_dir = sys.argv[2]
fallback_project_dir = sys.argv[3]
project_archive_dir = sys.argv[4]

begin = "<!-- AUTO-GOO-WIKI-ARCHIVE-BEGIN -->"
end = "<!-- AUTO-GOO-WIKI-ARCHIVE-END -->"
block = f"""{begin}
## AutoGoo / Goo-wiki 归档原则

- 本项目启用 Goo-wiki 作为项目记忆层；规划前先检索 `{wiki_dir}` 中相关项目页、概念页、周报和 `log.md`，复用已有约束、命令、路径、指标口径和历史经验。
- 使用 `/auto-goo:goo-plan` 生成计划时，必须在 `.goo/plan.json` 最后保留 `归档到 Goo-wiki` 步骤，并依赖所有非归档叶子步骤。
- 使用 `/auto-goo:goo-start` 或 `/auto-goo:goo-continue` 执行后，必须归档任务目标、计划摘要、步骤证据、产物路径、验证结果、关键决策、问题处理和可复用经验。
- 如果项目是 Git repo，必须在 Goo-wiki 项目页记录 git remote 地址，便于后续迁移、溯源和复用。
- Goo-wiki 可用时优先写入 `{wiki_dir}/{project_archive_dir}/` 并追加 `Goo-wiki/log.md`；不可用时写入 `{fallback_project_dir}` 作为本地 fallback。
- 不把归档当作事后报告；归档内容要能支撑下一次任务的召回、规划和复用。
{end}
"""

if target.exists():
    text = target.read_text(encoding="utf-8")
else:
    text = "# Project Instructions\n"

if begin in text and end in text:
    prefix, rest = text.split(begin, 1)
    _, suffix = rest.split(end, 1)
    new_text = prefix.rstrip() + "\n\n" + block + suffix.lstrip("\n")
else:
    new_text = text.rstrip() + "\n\n" + block

target.write_text(new_text, encoding="utf-8")
PY
    echo "Updated $PROJECT_CLAUDE_MD with Goo-wiki archive principles"
  fi
elif [[ "$SCOPE" == "project" && "$SKIP_CLAUDE_MD" -eq 1 ]]; then
  echo "Skipped project CLAUDE.md update (--skip-claude-md)"
elif [[ "$SCOPE" == "project" && "$WIKI_READY" -ne 1 ]]; then
  echo "Skipped project CLAUDE.md update because Goo-wiki CLAUDE.md was not found"
fi

echo ""
echo "Recommended SessionStart hook:"
cat <<'EOF'
{
  "hooks": {
    "SessionStart": [{
      "hooks": [
        {
          "type": "command",
          "command": "test -f \"${AUTO_GOO_WIKI_DIR:-$HOME/workspace/Goo-wiki}/CLAUDE.md\" && echo 'Goo-wiki vault ready' || echo 'Goo-wiki not found; using .goo/obsidian fallback'"
        },
        {
          "type": "command",
          "command": "cat .goo/plan.json 2>/dev/null && echo 'Unfinished AutoGoo plan found; run /auto-goo:goo-continue to resume' || true"
        }
      ]
    }]
  }
}
EOF
