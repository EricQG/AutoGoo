"""随机密码生成器 — 支持自定义长度和字符集。"""

import argparse
import secrets
import string


DEFAULT_LENGTH = 16
DEFAULT_CHARS = string.ascii_letters + string.digits + "!@#$%^&*"


def generate_password(length: int = DEFAULT_LENGTH, chars: str = DEFAULT_CHARS) -> str:
    """生成指定长度和字符集的随机密码。"""
    if length < 1:
        raise ValueError("Length must be >= 1")
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_passphrase(num_words: int = 4, separator: str = "-") -> str:
    """生成由常见单词组成的密码短语（更易记）。"""
    words = [
        "correct", "horse", "battery", "staple", "orange", "purple",
        "monkey", "diamond", "rocket", "coffee", "python", "forest",
        "ocean", "thunder", "silver", "golden", "crystal", "shadow",
    ]
    return separator.join(secrets.choice(words) for _ in range(num_words))


def grade_password(password: str) -> str:
    """评估密码强度。"""
    score = 0
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    if any(c.islower() for c in password) and any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*" for c in password):
        score += 1

    if score >= 5:
        return "非常强"
    elif score >= 3:
        return "强"
    elif score >= 2:
        return "中"
    else:
        return "弱"


def main() -> None:
    parser = argparse.ArgumentParser(description="随机密码生成器")
    parser.add_argument("-l", "--length", type=int, default=DEFAULT_LENGTH, help="密码长度")
    parser.add_argument("-c", "--chars", type=str, default=DEFAULT_CHARS, help="字符集")
    parser.add_argument("-n", "--num", type=int, default=5, help="生成数量")
    parser.add_argument("--passphrase", action="store_true", help="生成密码短语")
    args = parser.parse_args()

    if args.passphrase:
        for _ in range(args.num):
            pwd = generate_passphrase()
            print(f"  {pwd}  [{grade_password(pwd)}]")
    else:
        for _ in range(args.num):
            pwd = generate_password(args.length, args.chars)
            print(f"  {pwd}  [{grade_password(pwd)}]  ({args.length} chars)")


if __name__ == "__main__":
    main()
