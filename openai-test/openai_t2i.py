#!/usr/bin/env python
# coding: utf-8

import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from openai import OpenAI

# 从环境变量读取密钥；缺失时直接抛出明确错误信息
AGICTO_API_KEY: str | None = os.getenv("AGICTO_API_KEY")
if not AGICTO_API_KEY:
    raise ValueError("请先设置环境变量 AGICTO_API_KEY")

PROMPT = "湖边日落，唯美写实摄影，8k高清"
# 万相（阿里百炼）尺寸格式用 * 分隔，不是 OpenAI 的 1280x720
SIZE = "1280*720"

client = OpenAI(
    api_key=AGICTO_API_KEY,
    base_url="https://api.agicto.cn/v1",
)

# wan2.6-t2i 在网关上走阿里百炼多模态通道，请求体必须是 input.messages 结构，
# 直接传 OpenAI 原生的 prompt/size 会报 InvalidParameter: Field required: input.messages。
# 因此这里用 extra_body 透传百炼格式，并用 with_raw_response 取回原始响应。
raw = client.images.with_raw_response.generate(
    model="wan2.6-t2i",
    prompt=PROMPT,
    extra_body={
        "input": {
            "messages": [
                {"role": "user", "content": [{"text": PROMPT}]},
            ]
        },
        "parameters": {"size": SIZE, "n": 1},
    },
)

payload = json.loads(raw.text)
image_url: str = payload["output"]["choices"][0]["message"]["content"][0]["image"]

print(image_url)

# 网关返回的是带签名的临时地址，会过期，因此立即下载保存到脚本所在目录
output_dir = Path(__file__).resolve().parent
suffix = Path(urlparse(image_url).path).suffix or ".png"
output_path = output_dir / f"t2i_{datetime.now():%Y%m%d_%H%M%S}{suffix}"

with urllib.request.urlopen(image_url, timeout=120) as response:
    output_path.write_bytes(response.read())

print(f"图片已保存：{output_path}")
