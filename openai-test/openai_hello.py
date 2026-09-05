import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径，以便导入根目录下的公共模块
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

from env_loader import load_dotenv, require_env

# 加载 .env（自动按「入口脚本目录 -> 当前工作目录 -> 项目根目录」顺序查找）
load_dotenv()

client = OpenAI(
    api_key=require_env("AGICTO_API_KEY"),
    base_url="https://api.agicto.cn/v1/",
)

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": "你好，请用一句话介绍 AGICTO API。",
        }
    ],
)

print(completion.choices[0].message.content)
