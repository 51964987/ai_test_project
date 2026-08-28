"""
场景三：多轮对话 —— 连续追问同一张图
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

first_answer = completion.choices[0].message.content
print("第1轮回答：", first_answer)

if first_answer is None:
    raise RuntimeError("第 1 轮模型返回内容为空，无法继续多轮对话")

# 第 2 轮：把上一轮回答追加为 assistant，再追问（保留同一张图）
messages.append({"role": "assistant", "content": first_answer})
messages.append({
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "图中轮毂的位置在哪里"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://easycar.oss-cn-beijing.aliyuncs.com/car_undistorted.jpg"
            }
        }
    ]
})

completion = client.chat.completions.create(
    model="qwen-vl-plus",
    messages=messages
)

print("第2轮回答：", completion.choices[0].message.content)

# ============================================================
# 场景四（车险实战）：多轮定位车辆损伤位置
# 把上面的「轮毂定位」思路迁移到车险定损：先让模型整体描述车况，再追问并定位具体损伤位置。
# ============================================================

# 第 1 轮：整体车况描述
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "你是一名汽车保险定损专家。这是一张车辆照片，请描述车辆的外观状态，指出是否存在凹陷、划痕或破损等损伤。"
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
    model="qwen-vl-max-2024-08-09",
    messages=messages
)

first_answer = completion.choices[0].message.content
print("第1轮回答：", first_answer)

if first_answer is None:
    raise RuntimeError("第 1 轮模型返回内容为空，无法继续多轮对话")

# 第 2 轮：基于上文，追问损伤的具体坐标位置
messages.append({"role": "assistant", "content": first_answer})
messages.append({
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "框出图中凹陷和划痕的位置，并给出坐标。"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://easycar.oss-cn-beijing.aliyuncs.com/car_undistorted.jpg"
            }
        }
    ]
})

completion = client.chat.completions.create(
    model="qwen-vl-max-2024-08-09",
    messages=messages
)

print("第2轮回答：", completion.choices[0].message.content)