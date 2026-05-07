"""基线 JSON 序列化器 — 使用 Python 标准库 json 模块。

作为性能对比的 baseline。
"""

import json
from typing import Any


class BaselineSerializer:
    """基于 stdlib json 模块的序列化器。"""

    def __init__(self, ensure_ascii: bool = True, sort_keys: bool = False):
        self._ensure_ascii = ensure_ascii
        self._sort_keys = sort_keys

    @property
    def name(self) -> str:
        return "baseline(json)"

    def serialize(self, data: Any) -> bytes:
        return json.dumps(
            data,
            ensure_ascii=self._ensure_ascii,
            sort_keys=self._sort_keys,
        ).encode("utf-8")

    def deserialize(self, data: bytes) -> Any:
        return json.loads(data.decode("utf-8"))
