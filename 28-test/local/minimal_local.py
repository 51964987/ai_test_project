import os
import dashscope
from dashscope import MultiModalConversation

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY") or ""

local_file_path = "file://" + "D:/your/dir/1-Chinese-document-extraction.jpg".replace("\\", "/")
messages = [{
    "role": "user",
    "content": [
        {"image": local_file_path},
        {"text": "图片里有什么东西?"},
    ],
}]
response = MultiModalConversation.call(model="qwen-vl-plus", messages=messages)
print(response.output.choices[0].message.content[0]["text"])
