"""批量文件重命名工具 — 支持正则替换模式。

用法：
    python -m src.file_batch_rename.renamer <目录路径> <查找模式> <替换文本>

示例：
    python -m src.file_batch_rename.renamer . '\\.txt$' '.md'
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


def rename_files(
    directory: Path,
    find_pattern: str,
    replacement: str,
    dry_run: bool = False,
) -> List[Tuple[Path, Path]]:
    """在指定目录下对文件应用正则重命名。

    Args:
        directory: 目标目录路径。
        find_pattern: 用于匹配文件名的正则表达式。
        replacement: 替换文本（支持 re.sub 反向引用如 \\1）。
        dry_run: 若为 True 只打印不实际重命名。

    Returns:
        (原路径, 新路径) 变更列表。

    Raises:
        FileNotFoundError: directory 不存在或不是目录。
        re.error: find_pattern 不是合法正则。
    """
    if not directory.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"路径不是目录: {directory}")

    compiled: re.Pattern[str] = re.compile(find_pattern)
    changes: List[Tuple[Path, Path]] = []

    for entry in sorted(directory.iterdir()):
        if not entry.is_file():
            continue

        new_name: str = compiled.sub(replacement, entry.name)
        if new_name == entry.name:
            continue
        if not new_name:
            continue

        target: Path = entry.with_name(new_name)
        if target.exists():
            print(f"  [跳过] 目标已存在: {target.name}")
            continue

        changes.append((entry, target))

        if dry_run:
            print(f"  [试运行] {entry.name} -> {target.name}")
        else:
            entry.rename(target)
            print(f"  [已重命名] {entry.name} -> {target.name}")

    return changes


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="批量文件重命名工具 — 正则替换文件名",
    )
    parser.add_argument(
        "directory",
        type=str,
        help="目标目录路径",
    )
    parser.add_argument(
        "find_pattern",
        type=str,
        help="用于匹配文件名的正则表达式",
    )
    parser.add_argument(
        "replacement",
        type=str,
        help="替换文本（支持 \\1 等反向引用）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式，只打印不实际重命名",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    """CLI 入口。"""
    args = parse_args(argv)
    directory = Path(args.directory).resolve()

    try:
        changes = rename_files(
            directory=directory,
            find_pattern=args.find_pattern,
            replacement=args.replacement,
            dry_run=args.dry_run,
        )
    except (FileNotFoundError, NotADirectoryError, re.error) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        sys.exit(1)

    if not changes:
        print("无文件被匹配。")
        return

    print(f"\n共处理 {len(changes)} 个文件。")


if __name__ == "__main__":
    main()
