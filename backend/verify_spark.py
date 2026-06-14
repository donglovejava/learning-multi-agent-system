"""讯飞星火连通性独立验证脚本（不依赖 fastapi）。

用法：
    1. 在 backend/.env 填好 SPARK_API_PASSWORD（控制台 APIPassword）
    2. py verify_spark.py

成功会打印星火对一个测试问题的真实回复，并演示流式输出。
本脚本仅用于本地验证，不属于线上代码（已在 .gitignore 中忽略）。
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


def _load_env() -> None:
    """极简 .env 解析（避免依赖 python-dotenv）。"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("✗ 未找到 backend/.env，请先 cp .env.example .env 并填入 SPARK_API_PASSWORD")
        sys.exit(1)
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


async def main() -> None:
    _load_env()
    # 延迟导入：确保环境变量已就位再构造 settings
    from app.llm.spark_client import LLMError, SparkLLMClient

    pwd = os.environ.get("SPARK_API_PASSWORD", "")
    if not pwd:
        print("✗ .env 中 SPARK_API_PASSWORD 为空，请填入控制台 APIPassword")
        sys.exit(1)
    print(f"→ 使用 APIPassword: {pwd[:3]}***{pwd[-2:]}  model={os.environ.get('SPARK_MODEL', 'lite')}")

    client = SparkLLMClient()

    # 1. 非流式
    print("\n[1] 非流式 chat 测试 ...")
    try:
        reply = await client.chat("用一句话解释什么是注意力机制。")
        print("✓ 星火回复：", reply)
    except LLMError as exc:
        print("✗ 调用失败：", exc)
        sys.exit(1)

    # 2. 意图分类
    print("\n[2] 意图分类测试 ...")
    intent = await client.classify_intent("我想学 Transformer 的注意力机制")
    print(f"✓ 意图识别：{intent}（期望 generate_resource）")

    # 3. 知识点抽取
    print("\n[3] 知识点抽取测试 ...")
    kp = await client.extract_knowledge("我想学 Transformer 的注意力机制")
    print(f"✓ 抽取知识点：{kp}")

    # 4. 流式
    print("\n[4] 流式 chat_stream 测试 ...")
    print("✓ 流式输出：", end="", flush=True)
    async for token in client.chat_stream("数到5"):
        print(token, end="", flush=True)
    print("\n\n=== 全部通过，星火连通正常 ===")


if __name__ == "__main__":
    asyncio.run(main())
