"""LLM 输出 JSON 解析工具。

大模型常把 JSON 包在 ```json ... ``` 围栏里，或在前后附带说明文字。
本模块负责从这类「脏」文本中稳健地抽出 JSON 对象/数组并解析。
供 Quiz / MindMap 等需要结构化输出的 Agent 复用。
"""

from __future__ import annotations

import json
import re
from typing import Any

#: 匹配 ```json ... ``` 或 ``` ... ``` 代码围栏
_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> Any:
    """从 LLM 输出中抽取并解析 JSON。

    依次尝试：直接解析 → 去代码围栏后解析 → 截取首个 ``{...}`` / ``[...]`` 片段解析。
    全部失败抛 ``ValueError``，由调用方决定降级策略。
    """
    text = text.strip()

    # 1. 直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 去掉 markdown 代码围栏后解析
    fence = _FENCE_RE.search(text)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. 截取首个对象 / 数组片段（取最外层括号）
    snippet = _slice_outermost(text)
    if snippet:
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从 LLM 输出解析 JSON: {text[:200]}")


def _slice_outermost(text: str) -> str:
    """截取文本中最外层的 {...} 或 [...] 片段（按括号配平）。"""
    starts = {"{": "}", "[": "]"}
    for i, ch in enumerate(text):
        if ch in starts:
            close = starts[ch]
            depth = 0
            for j in range(i, len(text)):
                if text[j] == ch:
                    depth += 1
                elif text[j] == close:
                    depth -= 1
                    if depth == 0:
                        return text[i : j + 1]
            break
    return ""
