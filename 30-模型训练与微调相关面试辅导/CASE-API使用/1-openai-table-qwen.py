from openai.types.chat.chat_completion import ChatCompletion


import json
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("AGICTO_API_KEY"),
    base_url="https://api.agicto.cn/v1/",
)

# 封装模型响应函数
def get_response(messages):
    response: ChatCompletion = client.chat.completions.create(
        model="qwen3.5-plus",
        messages=messages,
    )
    return response

# 多模态消息：图片 URL + 文本（OpenAI 兼容格式）
content = [
    {"type": "image_url", "image_url": {"url": "https://aiwucai.oss-cn-huhehaote.aliyuncs.com/pdf_table.jpg"}},
    {"type": "text", "text": "这是一个表格图片，帮我提取里面的内容，输出JSON格式"},
]
messages = [{"role": "user", "content": content}]

# 得到响应
response = get_response(messages)
print(response)

# 输出内容
print(response.choices[0].message.content)

