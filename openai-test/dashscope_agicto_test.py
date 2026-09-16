#!/usr/bin/env python
# coding: utf-8

"""对比 DashScope 原生与 AGICTO 网关返回的图片向量，判断网关是否篡改了图片。

依赖环境变量（写入项目根目录的 .env，或在 PowerShell 中 $env:XXX='...'）：
    DASHSCOPE_API_KEY  阿里百炼（DashScope）的 API Key
    AGICTO_API_KEY     AGICTO 网关的 API Key
"""

import os
from http import HTTPStatus

import numpy as np
from dashscope import MultiModalEmbedding
from openai import OpenAI

# 从环境变量读取密钥；缺失时直接抛出明确错误信息
DASHSCOPE_API_KEY: str | None = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("请先设置环境变量 DASHSCOPE_API_KEY")

AGICTO_API_KEY: str | None = os.getenv("AGICTO_API_KEY")
if not AGICTO_API_KEY:
    raise ValueError("请先设置环境变量 AGICTO_API_KEY")

# ========= 配置区 =========
MODEL = "tongyi-embedding-vision-plus"
AGICTO_BASE_URL = "https://api.agicto.cn/v1"
TEST_IMAGE = "https://dashscope.oss-cn-beijing.aliyuncs.com/images/256_1.png"
# 判定「向量基本一致」的余弦相似度阈值
SIMILARITY_THRESHOLD = 0.999


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """计算两个向量的余弦相似度。"""
    a = np.array(vec_a)
    b = np.array(vec_b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# DashScope 原生
def get_dash_vec(img_url: str) -> list[float]:
    """调用 DashScope 原生多模态向量接口，返回图片的 embedding。"""
    resp = MultiModalEmbedding.call(
        api_key=DASHSCOPE_API_KEY,
        model=MODEL,
        input=[{"image": img_url}],
        res_level=1,
        dimension=1152,
    )
    if resp.status_code != HTTPStatus.OK:
        raise SystemExit(f"DashScope 调用失败：{resp.message}")
    embedding: list[float] = resp.output["embeddings"][0]["embedding"]
    return embedding


# AGICTO 网关
def get_agi_vec(img_url: str) -> list[float]:
    """经 AGICTO 网关调用同一个多模态向量模型，返回图片的 embedding。

    网关是 OpenAI 兼容代理，返回体可能是 OpenAI 的 data[] 结构，也可能是百炼
    原生的 output 结构；这里直接取原始 JSON 并做兼容解析，避免 SDK 在字段缺失时
    静默填充 None 而引发 AttributeError。
    """
    client = OpenAI(
        api_key=AGICTO_API_KEY,
        base_url=AGICTO_BASE_URL,
    )
    # cast_to=object 让 SDK 原样返回 JSON（dict），由我们自行兼容不同的返回结构。
    # 关键：网关把 /v1/embeddings 的 input 原样透传给百炼「多模态向量」接口，而百炼
    # 原生 HTTP 协议要求 input 是**对象** {"contents": [...]}（SDK 的 input 参数其实
    # 对应 HTTP 的 input.contents）。传列表 [{"image": url}]、字符串或 OpenAI 风格的
    # [{"type": "image", ...}] 都会报 BadRequest.IllegalInput: The input parameter
    # requires json format.（已实测，见 2026-09-16 排查记录）
    # 其余参数与 get_dash_vec 保持一致，才能与原生结果做公平对比。
    raw: object = client.post(
        "/embeddings",
        cast_to=object,
        body={
            "model": MODEL,
            "input": {"contents": [{"image": img_url}]},
            "parameters": {"dimension": 1152, "res_level": 1},
        },
    )
    if not isinstance(raw, dict):
        raise SystemExit(f"AGICTO 网关返回非预期类型：{type(raw).__name__}")

    # 错误响应（网关/百炼通用错误体：含 code/message，不含 data/output）
    if "data" not in raw and "output" not in raw:
        raise SystemExit(f"AGICTO 网关返回异常：{raw}")

    # OpenAI 兼容结构：data[].embedding
    if "data" in raw:
        data = raw["data"]
        if not isinstance(data, list) or not data:
            raise SystemExit(f"AGICTO 网关 data 字段异常：{data}")
        first = data[0]
        embedding = first.get("embedding") if isinstance(first, dict) else None
    # 百炼原生结构：output.embeddings[].embedding
    else:
        output = raw["output"]
        embeddings = output.get("embeddings") if isinstance(output, dict) else None
        if not isinstance(embeddings, list) or not embeddings:
            raise SystemExit(f"AGICTO 网关 output.embeddings 异常：{output}")
        first = embeddings[0]
        embedding = first.get("embedding") if isinstance(first, dict) else None

    if not embedding:
        raise SystemExit(f"AGICTO 网关未返回 embedding：{raw}")
    return embedding


def main() -> None:
    """分别取两侧向量并输出相似度，判断网关是否改动了图片。"""
    dash_vec = get_dash_vec(TEST_IMAGE)
    agi_vec = get_agi_vec(TEST_IMAGE)

    sim = cosine_similarity(dash_vec, agi_vec)
    print(f"\n===== 向量相似度：{sim:.6f} =====")
    if sim > SIMILARITY_THRESHOLD:
        print("向量基本一致，网关没有篡改图片")
    else:
        print("向量差异大，AGICTO 网关可能压缩/修改了图片，检索会出问题！")


if __name__ == "__main__":
    main()
