#!/usr/bin/env python
# coding: utf-8

import os

from openai import OpenAI

# 从环境变量读取密钥；缺失时直接抛出明确错误信息
AGICTO_API_KEY: str | None = os.getenv("AGICTO_API_KEY")
if not AGICTO_API_KEY:
    raise ValueError("请先设置环境变量 AGICTO_API_KEY")

client = OpenAI(
    api_key=AGICTO_API_KEY,
    base_url="https://api.agicto.cn/v1/",
)

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "你好，请用一句话介绍 AGICTO API。",
        }
    ],
)

print(completion.choices[0].message.content)
