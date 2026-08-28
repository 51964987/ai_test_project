"""
场景二：多图 —— 车辆身份核验（VIN / 车架号比对）
"""

import os

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# 显式标注为 SDK 官方类型，避免裸 dict 被推断成宽泛联合类型而触发类型报错
messages: list[ChatCompletionMessageParam] = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "你是一名汽车保险核保专家。这里有两张车辆身份核验证件图片。请分别提取每张图中的车架号（VIN）与发动机号，并判断两张图是否为同一车辆，最后给出核验结论（一致/不一致）及判断依据。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/11-vehicle-identity-verification-1.jpg"
                }
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/11-vehicle-identity-verification-2.jpg"
                }
            }
        ]
    }
]

completion = client.chat.completions.create(
    model="qwen-vl-max",
    messages=messages
)

print(completion.choices[0].message.content)
