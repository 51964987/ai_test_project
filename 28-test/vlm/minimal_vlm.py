"""最小可运行版本：读 prompt_template_cn.xlsx，逐行调 Qwen-VL，结果写回 Excel。

批量生产的完整版本（重试 / 并发 / 断点续跑 / 本地图片）见 batch_insurance_vlm.py。
"""
import os
from pathlib import Path

import pandas as pd
from openai import OpenAI
from openai.types.chat import ChatCompletionContentPartParam, ChatCompletionMessageParam

OSS_PREFIX = "https://vl-image.oss-cn-shanghai.aliyuncs.com"

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


def get_response(user_prompt: str, image_urls: list[str]) -> str:
    """一段文本 + N 张图片，返回模型的文本回复"""
    # 逐条 append 而非列表推导：推导式会退化成 dict[str, object]，无法通过 SDK 的 TypedDict 校验
    content: list[ChatCompletionContentPartParam] = [{"type": "text", "text": user_prompt}]
    for u in image_urls:
        content.append({"type": "image_url", "image_url": {"url": u}})
    messages: list[ChatCompletionMessageParam] = [{"role": "user", "content": content}]
    completion = client.chat.completions.create(
        model="qwen-vl-max",
        messages=messages,
    )
    return completion.choices[0].message.content or ""


def main() -> None:
    df = pd.read_excel("prompt_template_cn.xlsx")
    if "response" not in df.columns:
        df["response"] = ""
    # 全空的 response 列会被推断成 float64：一来 pandas 3.x 不允许往 float 列写字符串，
    # 二来 NaN 会让"是否已有结果"的判断失真（str(NaN) == "nan" 是 truthy），统一转空串
    df["response"] = df["response"].fillna("").astype(str)

    # iterrows 的索引类型是 Hashable，不能直接做 +1 算术，行号一律用 enumerate 生成
    for row_no, (index, row) in enumerate(df.iterrows(), 1):
        # Excel 里既可能填 policy_001 也可能填 policy_001.jpg，统一成带 .jpg 的文件名
        stem = Path(str(row["image"])).with_suffix(".jpg").name
        df.loc[index, "response"] = get_response(str(row["prompt"]), [f"{OSS_PREFIX}/{stem}"])
        print(f"{row_no} done")

    df.to_excel("prompt_template_cn_result.xlsx", index=False)


if __name__ == "__main__":
    main()
