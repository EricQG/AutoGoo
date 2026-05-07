#!/usr/bin/env python3
"""JSON 配置合并工具：合并两个 JSON 配置文件，后者覆盖前者同名键（深度合并一层）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="Merge two JSON config files (shallow merge, override wins)."
    )
    parser.add_argument(
        "--base",
        required=True,
        help="Path to the base JSON config file.",
    )
    parser.add_argument(
        "--override",
        required=True,
        help="Path to the override JSON config file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path for the merged output JSON file.",
    )
    return parser.parse_args(argv)


def load_json(path: str) -> dict[str, Any]:
    """加载并解析 JSON 文件，返回 dict。"""
    p = Path(path)
    if not p.exists():
        print(f"Error: file not found — {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with p.open("r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in {path} — {e}", file=sys.stderr)
        sys.exit(1)


def merge_shallow(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """一层深度合并：base 和 override 同级键合并，override 覆盖 base 同名键。"""
    merged: dict[str, Any] = {}
    # 先合并 base 的所有键
    for key, value in base.items():
        if key in override:
            merged[key] = override[key]
        else:
            merged[key] = value
    # 追加 override 中 base 没有的键
    for key, value in override.items():
        if key not in merged:
            merged[key] = value
    return merged


def write_json(data: dict[str, Any], path: str) -> None:
    """将 dict 以 JSON 格式写入文件（缩进 2 空格）。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Merged config written to {path}")


def main(argv: list[str] | None = None) -> None:
    """CLI 入口。"""
    args = parse_args(argv)
    base_data = load_json(args.base)
    override_data = load_json(args.override)
    merged = merge_shallow(base_data, override_data)
    write_json(merged, args.output)


if __name__ == "__main__":
    main()
