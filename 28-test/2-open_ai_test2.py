"""
场景二：视觉定位 —— 框出图中轮毂的位置
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
                "text": "框出图中轮毂的位置"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://easycar.oss-cn-beijing.aliyuncs.com/car_undistorted.jpg"
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