"""气温数据转换器：将 CSV 中的华氏度列转为摄氏度列。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="将 CSV 中的华氏度 (Fahrenheit) 转为摄氏度 (Celsius)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="输入 CSV 文件路径，需包含 Fahrenheit 列",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="输出 CSV 文件路径",
    )
    return parser.parse_args(argv)


def convert_fahrenheit_to_celsius(df: pd.DataFrame) -> pd.DataFrame:
    """将 DataFrame 中的 Fahrenheit 列转为 Celsius 列。

    Args:
        df: 包含 Fahrenheit 列的 DataFrame。

    Returns:
        新增了 Celsius 列的 DataFrame。
    """
    if "Fahrenheit" not in df.columns:
        msg = "输入 CSV 缺少 'Fahrenheit' 列"
        raise ValueError(msg)

    df = df.copy()
    df["Celsius"] = (df["Fahrenheit"] - 32) * 5.0 / 9.0
    return df


def main(argv: list[str] | None = None) -> None:
    """主入口：读取 CSV，转换温度，输出 CSV。"""
    args = parse_args(argv)

    if not args.input.exists():
        print(f"错误：输入文件不存在 — {args.input}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.input)
    result = convert_fahrenheit_to_celsius(df)
    result.to_csv(args.output, index=False)
    print(f"转换完成：{args.input} -> {args.output}")
    print(f"共处理 {len(result)} 行数据。")


if __name__ == "__main__":
    main()
