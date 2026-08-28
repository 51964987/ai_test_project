"""
场景三：多图 —— 承保验车（五视角外观审核）
"""
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    model="qwen-vl-max",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "你是一名汽车保险承保验车员。这里有同一辆车的五张外观照片（前、后、左、右及细节）。请逐张描述车辆外观状态，识别是否存在划痕、凹陷、破损等损伤，并综合判断该车是否满足承保条件，给出验车结论与风险提示。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/3-vehicle-underwriting-1.jpg"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/3-vehicle-underwriting-2.jpg"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/3-vehicle-underwriting-3.jpg"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/3-vehicle-underwriting-4.jpg"
                    }
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/3-vehicle-underwriting-5.jpg"
                    }
                }
            ]
        }
    ]
)

print(completion.choices[0].message.content)