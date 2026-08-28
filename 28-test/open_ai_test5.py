"""
场景五：单图 —— 危险驾驶行为检测
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
                    "text": "你是一名汽车保险风控专家。这是一张车内驾驶行为监控图片。请识别驾驶员是否存在危险驾驶行为（如未系安全带、手持手机、疲劳驾驶、抽烟等），列出检测到的行为及其风险等级，并给出风控建议。"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://vl-image.oss-cn-shanghai.aliyuncs.com/4-Dangerous-driving-behavior-detection.jpg"
                    }
                }
            ]
        }
    ]
)

print(completion.choices[0].message.content)