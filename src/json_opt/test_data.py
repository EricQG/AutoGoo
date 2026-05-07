"""合成测试数据生成器。

生成至少 1 万条记录的复杂 JSON 测试数据，模拟真实场景：
- 混合类型：字符串、数字、布尔、嵌套对象、数组、空值
- 模拟电商订单/用户数据
"""

import random
import string
import time
from typing import Any


def random_string(min_len: int = 5, max_len: int = 50) -> str:
    length = random.randint(min_len, max_len)
    return "".join(random.choices(string.ascii_letters + string.digits + " ", k=length))


def random_email() -> str:
    name = random_string(5, 15).replace(" ", "_").lower()
    domain = random_string(3, 8).lower()
    tld = random.choice(["com", "org", "net", "io", "cn"])
    return f"{name}@{domain}.{tld}"


def random_phone() -> str:
    return f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


def generate_order() -> dict[str, Any]:
    """生成一个模拟订单记录。"""
    items_count = random.randint(1, 6)
    items = []
    for _ in range(items_count):
        items.append({
            "product_id": f"PROD-{random.randint(10000, 99999)}",
            "name": random_string(8, 30),
            "quantity": random.randint(1, 5),
            "unit_price": round(random.uniform(5.99, 999.99), 2),
            "category": random.choice(["electronics", "clothing", "food", "books", "sports"]),
            "tags": random.sample(["new", "sale", "popular", "limited", "clearance", "premium"],
                                   k=random.randint(0, 3)),
        })

    subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
    tax_rate = random.choice([0.05, 0.08, 0.10, 0.13])
    return {
        "order_id": f"ORD-{random.randint(100000, 999999)}",
        "customer": {
            "id": f"CUST-{random.randint(1000, 9999)}",
            "name": random_string(8, 25),
            "email": random_email(),
            "phone": random_phone(),
            "address": {
                "street": f"{random.randint(1, 9999)} {random_string(8, 20)}",
                "city": random_string(6, 15),
                "state": random.choice(["CA", "NY", "TX", "FL", "IL", "WA", "MA", "CO"]),
                "zip": f"{random.randint(10000, 99999)}",
                "country": "US",
            },
            "loyalty_tier": random.choice(["bronze", "silver", "gold", "platinum"]),
        },
        "items": items,
        "subtotal": round(subtotal, 2),
        "tax": round(subtotal * tax_rate, 2),
        "total": round(subtotal * (1 + tax_rate), 2),
        "currency": "USD",
        "status": random.choice(["pending", "processing", "shipped", "delivered", "cancelled"]),
        "created_at": f"2026-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}T"
                      f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}Z",
        "notes": random_string(0, 200) if random.random() > 0.3 else None,
    }


def generate_orders(count: int = 10000) -> list[dict[str, Any]]:
    """生成指定数量的订单记录。"""
    random.seed(42)  # 可复现
    return [generate_order() for _ in range(count)]


def generate_large_nested() -> dict[str, Any]:
    """生成一个大型嵌套 JSON 结构（模拟配置/参数文件）。"""
    def _make_tree(depth: int, breadth: int) -> Any:
        if depth <= 0:
            return random_string(5, 20)
        return {
            f"key_{i}_{_make_tree(depth - 1, breadth)}": _make_tree(depth - 1, breadth)
            for i in range(breadth)
        }
    return _make_tree(4, 3)


if __name__ == "__main__":
    # 测试数据生成
    orders = generate_orders(1000)
    print(f"Generated {len(orders)} orders")
    print(f"Sample order keys: {list(orders[0].keys())}")
    print(f"Sample order: {orders[0]}")

    large = generate_large_nested()
    print(f"Large nested keys: {list(large.keys())[:5]}")
