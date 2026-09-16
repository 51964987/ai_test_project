#!/usr/bin/env python
# coding: utf-8

import os

from openai import OpenAI

# DeepSeek-V4.1-Flash 的官方调用名是 deepseek-flash
# deepseek-v4.1-flash 不是 API 模型名，官方不会识别
MODEL = "deepseek-flash"

# 从环境变量读取密钥；缺失时直接抛出明确错误信息
DEEPSEEK_API_KEY: str | None = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("请先设置环境变量 DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

# 文字输出
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "用中文解释AI大模型是如何工作的"}],
)

print(response.choices[0].message.content)
