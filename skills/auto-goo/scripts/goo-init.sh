#!/usr/bin/env bash
# AutoGoo: interactive configuration initializer
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  goo-init.sh [--user|--project] [--wiki-dir PATH] [--yes] [--force]

Options:
  --user            Write user-level config to ~/.auto-goo/config.json
  --project         Write project-level config to .goo/config.json
  --wiki-dir PATH   Set Goo-wiki directory (default: ~/workspace/Goo-wiki)
  --yes             Use defaults for unanswered prompts
  --force           Overwrite existing config without asking
  -h, --help        Show this help
EOF
}

SCOPE=""
WIKI_DIR="${AUTO_GOO_WIKI_DIR:-}"
WIKI_DIR_PROVIDED=0
YES=0
FORCE=0

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
    --yes|-y)
      YES=1
      shift
      ;;
    --force)
      FORCE=1
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

echo ""
echo "AutoGoo init"
echo "  scope:      $SCOPE"
echo "  config:     $CONFIG_FILE"
echo "  wiki_dir:   $WIKI_DIR"

if [[ -f "$WIKI_DIR_EXPANDED/CLAUDE.md" ]]; then
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

mkdir -p "$CONFIG_DIR"

python3 - "$CONFIG_FILE" "$WIKI_DIR" "$FALLBACK_DIR" <<'PY'
import json
import sys
from pathlib import Path

target = Path(sys.argv[1])
wiki_dir = sys.argv[2]
fallback_dir = sys.argv[3]

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

target.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

echo ""
echo "Wrote $CONFIG_FILE"
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
