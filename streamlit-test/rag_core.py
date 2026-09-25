#!/usr/bin/env python
# coding: utf-8

"""RAG 核心能力层：文档解析 -> 文本切分 -> 向量化 -> 相似度检索 -> 大模型生成。

只依赖 openai / numpy / pypdf，UI 相关逻辑全部放在 rag_app.py 中，便于单独测试。
"""

from __future__ import annotations

import io
import os
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import numpy as np
from openai import OpenAI
from pypdf import PdfReader

# AGICTO 网关（OpenAI 兼容协议）
AGICTO_BASE_URL = "https://api.agicto.cn/v1"
DEFAULT_CHAT_MODEL = "qwen-plus"
DEFAULT_EMBED_MODEL = "text-embedding-v3"

# 网关对 embedding 的批量条数限制较保守，这里每批最多 10 条
EMBED_BATCH_SIZE = 10

SYSTEM_PROMPT = (
    "你是严谨的中文问答助手。回答要简洁、分点清晰，不要编造信息。"
)

# 内置示例知识库：无需上传文件即可体验完整 RAG 流程
SAMPLE_DOCS: dict[str, str] = {
    "RAG技术白皮书（示例）": """RAG（Retrieval-Augmented Generation，检索增强生成）是一种把"信息检索"与"大语言模型生成"结合的技术方案。
它的核心流程分为三步：第一是索引阶段，把原始文档切分成较小的片段，并用向量模型把每个片段编码成向量，存入向量库；
第二是检索阶段，把用户的问题也编码成向量，在向量库中按余弦相似度找出最相关的若干片段；
第三是生成阶段，把检索到的片段作为参考资料拼进提示词，让大模型基于这些资料组织答案。

相比直接向大模型提问，RAG 有三个明显优势。
其一，可以接入私有或实时资料，突破模型训练数据的时效与范围限制。
其二，答案可以标注引用来源，便于人工核对，降低模型幻觉带来的风险。
其三，更新知识的成本极低：只需重新索引文档，无需重新训练或微调模型。

RAG 的效果高度依赖切分策略。片段过长会引入无关噪声并挤占上下文窗口，
片段过短又会切断语义，导致检索命中率下降。工程上常用 300 到 500 字的窗口，
并保留 50 到 100 字的重叠区域，让跨片段的话题仍能被完整召回。

RAG 也并非万能。它无法解决"资料里根本没有答案"的问题，
也无法替代需要多步推理或复杂计算的场景。这类场景通常需要引入 Agent、
工具调用或查询改写（Query Rewriting）等进阶手段进行补充。""",
    "AGICTO网关使用说明（示例）": """AGICTO 是一个大模型 API 中转网关，对外提供 OpenAI 兼容的 HTTP 接口。
使用时只需把 base_url 指向 https://api.agicto.cn/v1，并把 api_key 换成网关密钥，
即可沿用 OpenAI 官方 SDK 的调用方式，无需改造业务代码。

网关常用的两个接口是对话补全与文本向量。
对话补全对应 /v1/chat/completions，传入 model、messages 即可，
把 stream 设为 true 还能逐字流式返回，适合做网页端的打字机效果。
文本向量对应 /v1/embeddings，传入 model 与 input（字符串数组）即可拿到浮点数组。

需要注意的是，网关只是转发请求，真正的模型能力由上游厂商提供。
因此模型名必须使用上游厂商公布的正式名称，例如通义千问系列应写 qwen-plus，
而不是自定义的别名。遇到参数类报错时，也应当以上游官方文档为准进行排查。""",
}


def get_api_key() -> str:
    """从环境变量读取网关密钥，缺失时给出明确报错。"""
    api_key: str | None = os.getenv("AGICTO_API_KEY")
    if not api_key:
        raise ValueError("请先设置环境变量 AGICTO_API_KEY")
    return api_key


def build_client(api_key: str) -> OpenAI:
    """创建指向 AGICTO 网关的 OpenAI 兼容客户端。"""
    return OpenAI(api_key=api_key, base_url=AGICTO_BASE_URL)


@dataclass(slots=True)
class Chunk:
    """一个知识片段：文本 + 来源 + 在该来源中的序号。"""

    text: str
    source: str
    index: int


@dataclass(slots=True)
class KnowledgeBase:
    """内存版向量库：片段列表 + 已归一化的向量矩阵。"""

    chunks: list[Chunk]
    matrix: np.ndarray
    embed_model: str

    @property
    def size(self) -> int:
        """知识库中的片段数量。"""
        return len(self.chunks)


@dataclass(slots=True)
class Hit:
    """一次检索的命中结果。"""

    chunk: Chunk
    score: float


def read_pdf(stream: io.BytesIO) -> str:
    """读取 PDF 文件的纯文本内容。"""
    text: str = "\n".join(
        (page.extract_text() or "") for page in PdfReader(stream).pages
    )
    return text.strip()


def read_uploaded_file(file_name: str, file_bytes: bytes) -> str:
    """按扩展名解析上传文件，返回纯文本。

    支持 .txt / .md / .pdf，其它扩展名按 UTF-8 文本处理。
    """
    if file_name.lower().endswith(".pdf"):
        return read_pdf(io.BytesIO(file_bytes))

    text: str = file_bytes.decode("utf-8", errors="ignore")
    return text.strip()


def split_text(text: str, chunk_size: int = 350, overlap: int = 60) -> list[str]:
    """把长文本切成带重叠的定长片段（按字符计数，对中文友好）。

    采用滑窗而非"先断句再拼接"，保证片段长度可控、重叠比例稳定。
    """
    cleaned: str = re.sub(r"[ \t]+", " ", text.strip())
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    if not cleaned:
        return []

    step: int = max(1, chunk_size - overlap)
    chunks: list[str] = [
        cleaned[start : start + chunk_size]
        for start in range(0, len(cleaned), step)
    ]
    # 丢弃尾部过短的碎片（不足chunk_size的一半），它们通常无法独立表达语义
    min_len: int = max(20, chunk_size // 2)
    return [c for c in chunks if len(c) >= min_len or len(chunks) == 1]


def embed_texts(client: OpenAI, model: str, texts: list[str]) -> np.ndarray:
    """批量把文本转成向量，返回按行归一化后的二维矩阵。"""
    vectors: list[list[float]] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch: list[str] = texts[start : start + EMBED_BATCH_SIZE]
        resp = client.embeddings.create(model=model, input=batch)
        if len(resp.data) != len(batch):
            raise RuntimeError(
                f"向量接口返回条数异常：期望 {len(batch)} 条，实际 {len(resp.data)} 条"
            )
        vectors.extend(item.embedding for item in resp.data)

    matrix: np.ndarray = np.asarray(vectors, dtype=np.float32)
    norms: np.ndarray = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build_knowledge_base(
    client: OpenAI,
    docs: dict[str, str],
    embed_model: str,
    chunk_size: int,
    overlap: int,
    on_progress: Callable[[int, int], None] | None = None,
) -> KnowledgeBase:
    """把 {来源名: 原文} 切分并向量化，构建内存向量库。"""
    chunks: list[Chunk] = []
    for source, text in docs.items():
        for index, piece in enumerate(split_text(text, chunk_size, overlap)):
            chunks.append(Chunk(text=piece, source=source, index=index))

    if not chunks:
        raise ValueError("没有从文档中提取到任何文本，请检查文件内容")

    texts: list[str] = [c.text for c in chunks]
    vectors: list[np.ndarray] = []
    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch: list[str] = texts[start : start + EMBED_BATCH_SIZE]
        vectors.append(embed_texts(client, embed_model, batch))
        if on_progress is not None:
            on_progress(min(start + EMBED_BATCH_SIZE, len(texts)), len(texts))

    return KnowledgeBase(
        chunks=chunks,
        matrix=np.vstack(vectors),
        embed_model=embed_model,
    )


def search(
    client: OpenAI,
    kb: KnowledgeBase,
    query: str,
    top_k: int,
) -> list[Hit]:
    """在知识库中检索与问题最相关的 top_k 个片段。"""
    query_vec: np.ndarray = embed_texts(client, kb.embed_model, [query])[0]
    scores: np.ndarray = kb.matrix @ query_vec  # 已归一化，点积即余弦相似度
    top_indexes: np.ndarray = np.argsort(scores)[::-1][:top_k]
    return [Hit(chunk=kb.chunks[int(i)], score=float(scores[int(i)])) for i in top_indexes]


def build_context(hits: list[Hit]) -> str:
    """把命中片段拼成带编号的参考资料文本。"""
    parts: list[str] = []
    for number, hit in enumerate(hits, start=1):
        parts.append(
            f"[{number}] 来源：{hit.chunk.source}（相似度 {hit.score:.3f}）\n{hit.chunk.text}"
        )
    return "\n\n".join(parts)


def build_messages(
    query: str,
    hits: list[Hit],
    history: list[dict[str, str]],
    enable_rag: bool,
) -> list[dict[str, str]]:
    """组装发给大模型的消息列表：系统提示 + 最近的对话历史 + 当前问题。"""
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 只带最近 6 条历史，且不带上下文，避免提示词无限膨胀
    messages.extend(history[-6:])

    if enable_rag and hits:
        user_content: str = (
            "请严格依据下列参考资料回答问题；如果资料中没有答案，"
            "请直接回答「参考资料中没有相关信息」，不要编造。\n\n"
            f"参考资料：\n{build_context(hits)}\n\n问题：{query}"
        )
    else:
        user_content = query

    messages.append({"role": "user", "content": user_content})
    return messages


def stream_answer(
    client: OpenAI,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
) -> Iterator[str]:
    """以流式方式调用对话接口，逐段产出文本。"""
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    for part in resp:
        if not part.choices:
            continue
        content: str | None = part.choices[0].delta.content
        if content:
            yield content
