"""
场景四：单图 —— 事故要素抽取
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
                "text": "你是一名汽车保险理赔定损专家。这是一张交通事故现场图片。请抽取事故关键要素：事故类型、涉及车辆数量、碰撞部位、损伤程度、是否涉及人员伤亡、是否存在第三方财产损失，并以条目化形式输出。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/10-extraction-of-auto-accident-elements.jpg"
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
