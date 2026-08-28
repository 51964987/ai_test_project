"""
场景一：单图 —— 车辆里程表读数识别
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
                "text": "你是一名汽车保险承保专家。这里有一张车辆里程表的图片。请从中提取关键信息，输出车辆当前总里程数（单位：公里），并说明仪表类型是机械式还是液晶式。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/1-vehicle-odometer-reading.jpg"
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