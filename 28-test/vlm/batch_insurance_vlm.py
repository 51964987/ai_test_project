#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pyright: reportUnusedCallResult=false
# pyright: reportUninitializedInstanceVariable=false
"""
batch_insurance_vlm.py
批量保险单证多模态信息抽取（Qwen-VL · OpenAI 兼容模式 · Excel 驱动）

依赖：pip install openai pandas openpyxl
环境：export DASHSCOPE_API_KEY=sk-xxxx     (Windows PowerShell: $env:DASHSCOPE_API_KEY="sk-xxxx")

用法：
    python batch_insurance_vlm.py --oss
    python batch_insurance_vlm.py --oss --save-every
    python batch_insurance_vlm.py --input D:/data/in.xlsx --output D:/data/out.xlsx \
                                  --image-dir ./images --model qwen-vl-max

默认的输入/输出文件位于脚本同级目录，因此从任意工作目录运行都能定位到。
"""

import argparse
import base64
import mimetypes
import os
import sys
import time
from pathlib import Path

import pandas as pd
from openai import APIStatusError, OpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
)

BASE_URL      = "https://dashscope.aliyuncs.com/compatible-mode/v1"
OSS_PREFIX    = "https://vl-image.oss-cn-shanghai.aliyuncs.com"   # 教程示例 OSS，生产请替换
DEFAULT_MODEL = "qwen-vl-max"

# 模板与结果文件放在脚本同级目录，用绝对路径兜底，避免工作目录不同导致找不到文件
SCRIPT_DIR     = Path(__file__).resolve().parent
DEFAULT_INPUT  = str(SCRIPT_DIR / "prompt_template_cn.xlsx")
DEFAULT_OUTPUT = str(SCRIPT_DIR / "prompt_template_cn_result.xlsx")
DEFAULT_IMAGE_DIR = str(SCRIPT_DIR / "images")

# Excel 的 image 列常常省略扩展名，本地查找时按这个顺序补全
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff")

client = OpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"), base_url=BASE_URL)


def image_to_data_url(path: str | Path) -> str:
    """本地图片转 Data URL（Base64），适用于本地单证影像件"""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"图片不存在: {p}")
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def find_local_image(image_dir: str | Path, name: str) -> Path | None:
    """在 image_dir 下按图片名查找，名字带不带扩展名都支持，找不到返回 None"""
    p = Path(image_dir) / name
    if p.is_file():
        return p
    if p.suffix:      # 已带扩展名却找不到，就不再猜其他后缀
        return None
    for ext in IMAGE_EXTS:
        cand = p.with_suffix(ext)
        if cand.is_file():
            return cand
    return None


def build_image_urls(
    image_field: object, image_dir: str | Path = ".", use_oss: bool = False
) -> list[str]:
    """解析 Excel 的 image 列，单个名字按以下顺序判定来源：
       1) http:// / https:// / data: 开头   完整的远程 URL / Data URL，原样使用
       2) --oss                            OSS 图片名，拼前缀并补 .jpg
       3) 本地能找到                        读取本地图转 Base64（自动补全扩展名）
       4) 本地找不到且名字没有扩展名          按 OSS 图片名处理
       5) 其余（有扩展名但本地找不到）        直接报错，不猜
    """
    field = str(image_field).strip()
    if field.startswith("[") and field.endswith("]"):
        names = [x.strip().strip("'\"") for x in field[1:-1].split(",") if x.strip()]
    else:
        names = [field]

    def to_oss_url(name: str) -> str:
        # Excel 里既可能填 policy_001 也可能填 policy_001.jpg，统一成带 .jpg 的文件名
        return f"{OSS_PREFIX}/{Path(name).with_suffix('.jpg').name}"

    urls: list[str] = []
    for name in names:
        if name.startswith(("http://", "https://", "data:")):
            urls.append(name)
        elif use_oss:
            urls.append(to_oss_url(name))
        else:
            local = find_local_image(image_dir, name)
            if local is not None:
                urls.append(image_to_data_url(local))
            elif not Path(name).suffix:
                urls.append(to_oss_url(name))
            else:
                tip = "若填的是 OSS 图片名请加 --oss，若填的是本地相对路径请用 --image-dir 指定目录"
                missing = (Path(image_dir) / name).resolve()
                raise FileNotFoundError(f"图片不存在: {missing}；{tip}")
    return urls


def build_messages(prompt: str, image_urls: list[str]) -> list[ChatCompletionMessageParam]:
    """构造多模态消息：一段文本 + N 张图片"""
    # 逐条 append 而非列表推导：推导式会退化成 dict[str, object]，无法通过 SDK 的 TypedDict 校验
    content: list[ChatCompletionContentPartParam] = [{"type": "text", "text": prompt}]
    for u in image_urls:
        content.append({"type": "image_url", "image_url": {"url": u}})
    return [{"role": "user", "content": content}]


def get_response(
    prompt: str,
    image_urls: list[str],
    model: str = DEFAULT_MODEL,
    retries: int = 3,
    timeout: int = 180,
) -> ChatCompletion:
    """带指数退避重试的 VLM 调用"""
    last_err = None
    for attempt in range(retries):
        try:
            return client.chat.completions.create(
                model=model,
                messages=build_messages(prompt, image_urls),
                timeout=timeout,
                # 高分辨率模式：保留保单/发票上的小字细节，非 OpenAI 标准参数需放 extra_body
                extra_body={"vl_high_resolution_images": True},
            )
        except Exception as e:
            # 4xx（429 限流除外）是参数/权限类永久错误，重试只是白等，直接抛出
            if isinstance(e, APIStatusError) and 400 <= e.status_code < 500:
                if e.status_code != 429:
                    raise
            last_err = e
            wait = int(2**attempt)   # int ** int 在 typeshed 里推断为 Any，显式转回 int
            print(f"  第 {attempt + 1} 次调用失败：{e}，{wait}s 后重试")
            time.sleep(wait)
    raise RuntimeError(f"调用失败（已重试 {retries} 次）：{last_err}")


def run(
    input_file: str,
    output_file: str,
    image_dir: str,
    model: str,
    use_oss: bool,
    save_every: bool,
) -> None:
    if not os.getenv("DASHSCOPE_API_KEY"):
        sys.exit("请先设置环境变量 DASHSCOPE_API_KEY")

    input_path = Path(input_file)
    if not input_path.is_file():
        hint = "请用 --input 指定，或先运行同目录的 make_template.py 生成示例模板"
        sys.exit(f"输入文件不存在：{input_path.resolve()}\n{hint}")

    df = pd.read_excel(input_file)
    for col in ("prompt", "image"):
        if col not in df.columns:
            sys.exit(f"Excel 缺少必需列：{col}")
    if "response" not in df.columns:
        df["response"] = ""
    # 全空的 response 列会被推断成 float64：一来 pandas 3.x 不允许往 float 列写字符串，
    # 二来 NaN 会让"是否已有结果"的判断失真（str(NaN) == "nan" 是 truthy），统一转空串
    df["response"] = df["response"].fillna("").astype(str)

    total = len(df)
    # iterrows 的索引类型是 Hashable，不能直接做 +1 算术，行号一律用 enumerate 生成
    for row_no, (idx, row) in enumerate(df.iterrows(), 1):
        if str(row["response"]).strip():      # 断点续跑：已有结果直接跳过
            print(f"[{row_no}/{total}] 已有结果，跳过")
            continue

        prompt = str(row["prompt"])
        urls = build_image_urls(row["image"], image_dir, use_oss)
        try:
            completion = get_response(prompt, urls, model=model)
        except Exception as e:
            sys.exit(f"[{row_no}/{total}] 调用失败：{e}")   # 带行号，便于定位是哪行数据有问题

        # content 在 SDK 中是可选字段，取不到时写空串，避免把 None 落进 Excel
        answer = completion.choices[0].message.content or ""
        df.at[idx, "response"] = answer
        # SDK 把 usage 声明为可选字段，缺失时按 0 计，不影响主流程
        tokens = completion.usage.total_tokens if completion.usage else 0
        print(f"[{row_no}/{total}] 完成，tokens={tokens}")
        print(answer)
        print("-" * 60)

        if save_every:                                     # 增量落盘，防止长任务中断丢结果
            df.to_excel(output_file, index=False)

    df.to_excel(output_file, index=False)
    print(f"全部完成，结果已写入 {output_file}")


class Args(argparse.Namespace):
    """给 argparse 结果补上静态类型，避免 Namespace 属性一律退化成 Any

    这里只声明不赋值：argparse 只在属性不存在时才注入 default，
    一旦类里预置了默认值，add_argument 的 default 就会被整个跳过。
    """

    input: str
    output: str
    image_dir: str
    model: str
    oss: bool
    save_every: bool


def main() -> None:
    ap = argparse.ArgumentParser(description="批量保险单证多模态信息抽取")
    ap.add_argument("--input",      default=DEFAULT_INPUT,  help="输入 Excel（含 prompt / image 列），默认脚本同级目录")
    ap.add_argument("--output",     default=DEFAULT_OUTPUT, help="输出 Excel，默认脚本同级目录")
    ap.add_argument("--image-dir",  default=DEFAULT_IMAGE_DIR, help="本地图片目录，默认脚本同级的 images")
    ap.add_argument("--model",      default=DEFAULT_MODEL,                     help="qwen-vl-max / qwen-vl-plus")
    ap.add_argument("--oss",        action="store_true",                     help="image 列填的是 OSS 图片名（拼接前缀）")
    ap.add_argument("--save-every", action="store_true",                     help="每行都落盘，防止中断丢结果")
    args = ap.parse_args(namespace=Args())

    run(
        input_file=args.input,
        output_file=args.output,
        image_dir=args.image_dir,
        model=args.model,
        use_oss=args.oss,
        save_every=args.save_every,
    )


if __name__ == "__main__":
    main()
