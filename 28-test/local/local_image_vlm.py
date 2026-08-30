#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
local_image_vlm.py
本地图片多模态理解（Qwen-VL · DashScope 原生 SDK）

依赖：pip install dashscope
环境：export DASHSCOPE_API_KEY=sk-xxxx   (Windows PowerShell: $env:DASHSCOPE_API_KEY="sk-xxxx")

用法：
    python local_image_vlm.py 1-Chinese-document-extraction.jpg
    python local_image_vlm.py ./images --question "提取图中所有字段，以 JSON 输出"
    python local_image_vlm.py ./images --merge          # 多张图合并成一次请求
    python local_image_vlm.py 2-Japanese-document-extraction.jpg --mode base64 --model qwen-vl-max
"""

import argparse
import base64
import mimetypes
import os
import sys
from collections.abc import Iterable
from pathlib import Path

import dashscope
from dashscope import MultiModalConversation
from dashscope.api_entities.dashscope_response import MultiModalConversationResponse

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY") or ""

SUPPORTED: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}


def to_file_url(path: str | Path) -> str:
    """本地路径转 file:// URL。
       Windows : file://D:/images/test.png
       Linux/macOS: file:///home/images/test.png
    """
    abs_path = str(Path(path).resolve()).replace("\\", "/")
    return "file://" + abs_path


def to_data_url(path: str | Path) -> str:
    """本地图片转 Data URL（Base64），跨平台/跨网络环境最稳妥"""
    p = Path(path)
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    b64 = base64.b64encode(p.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def check(response: MultiModalConversationResponse) -> MultiModalConversationResponse:
    """统一校验 DashScope 响应状态码，把错误暴露清楚"""
    if response.status_code != 200:
        raise RuntimeError(
            f"调用失败 [request_id={response.request_id}] "
            f"code={response.code} message={response.message}"
        )
    return response


def ask(
    image_path: str | Path,
    question: str,
    model: str = "qwen-vl-plus",
    mode: str = "file",
) -> str:
    """单张图片问答。mode=file 走 file:// 路径，mode=base64 走 Base64"""
    if mode == "file":
        image_item: dict[str, str] = {"image": to_file_url(image_path)}
    else:
        image_item = {"image": to_data_url(image_path)}

    messages = [{"role": "user", "content": [image_item, {"text": question}]}]
    response = check(MultiModalConversation.call(model=model, messages=messages))
    return response.output.choices[0].message.content[0]["text"]


def ask_multi(
    image_paths: Iterable[str | Path],
    question: str,
    model: str = "qwen-vl-plus",
) -> str:
    """多张图一次请求（如身份证正反面、多页保单、多页体检报告）"""
    content: list[dict[str, str]] = [{"image": to_file_url(p)} for p in image_paths]
    content.append({"text": question})
    response = check(MultiModalConversation.call(
        model=model,
        messages=[{"role": "user", "content": content}],
        vl_high_resolution_images=True,   # DashScope SDK 可直接作为顶层参数
    ))
    return response.output.choices[0].message.content[0]["text"]


def main():
    ap = argparse.ArgumentParser(description="本地图片 VLM 识别（Qwen-VL）")
    ap.add_argument("target", help="图片文件或图片目录")
    ap.add_argument("--question", default="图片里有什么东西?")
    ap.add_argument("--model", default="qwen-vl-plus", help="qwen-vl-plus / qwen-vl-max")
    ap.add_argument("--mode", choices=["file", "base64"], default="file")
    ap.add_argument("--merge", action="store_true", help="目录模式下把多张图合并为一次请求")
    args = ap.parse_args()

    if not dashscope.api_key:
        sys.exit("请先设置环境变量 DASHSCOPE_API_KEY")

    target = Path(args.target)
    if target.is_dir():
        images = sorted(p for p in target.iterdir() if p.suffix.lower() in SUPPORTED)
        if not images:
            sys.exit(f"目录中没有受支持的图片：{target}")
        if args.merge:
            print(ask_multi(images, args.question, args.model))
        else:
            for img in images:
                print(f"===== {img.name} =====")
                print(ask(img, args.question, args.model, args.mode))
    else:
        if not target.is_file():
            sys.exit(f"文件不存在：{target}")
        print(ask(target, args.question, args.model, args.mode))


if __name__ == "__main__":
    main()
