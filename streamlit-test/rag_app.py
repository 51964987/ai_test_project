#!/usr/bin/env python
# coding: utf-8

"""RAG 大模型问答网页 Demo（Streamlit）。

运行方式（Windows PowerShell）：
    pip install -r streamlit-test/requirements.txt
    $env:AGICTO_API_KEY='你的网关密钥'
    streamlit run streamlit-test/rag_app.py
"""

from __future__ import annotations

import os
from typing import Any

import streamlit as st

from rag_core import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_EMBED_MODEL,
    SAMPLE_DOCS,
    Chunk,
    Hit,
    KnowledgeBase,
    build_client,
    build_knowledge_base,
    build_messages,
    get_api_key,
    read_uploaded_file,
    search,
    stream_answer,
)

# ========= 环境变量：密钥只从环境变量读取 =========
API_KEY: str | None = os.getenv("AGICTO_API_KEY")
if not API_KEY:
    st.error(
        "未检测到环境变量 AGICTO_API_KEY。\n\n"
        "请先在 PowerShell 中执行：\n\n"
        "    $env:AGICTO_API_KEY='你的网关密钥'\n\n"
        "然后重新启动本应用。"
    )
    st.stop()

CLIENT = build_client(API_KEY)

st.set_page_config(page_title="RAG 大模型问答 Demo", layout="wide")


def init_state() -> None:
    """初始化会话状态。"""
    st.session_state.setdefault("messages", [])  # 对话历史（不含上下文）
    st.session_state.setdefault("kb", None)  # 内存向量库


def render_sidebar() -> dict[str, Any]:
    """渲染侧边栏：模型参数 + 知识库构建区，返回参数字典。"""
    st.header("参数配置")

    chat_model: str = st.text_input("对话模型", value=DEFAULT_CHAT_MODEL)
    embed_model: str = st.text_input("向量模型", value=DEFAULT_EMBED_MODEL)
    temperature: float = st.slider("生成温度", 0.0, 1.0, 0.2, 0.1)
    top_k: int = st.slider("检索条数 top_k", 1, 8, 3)
    chunk_size: int = st.slider("片段长度（字）", 100, 800, 350, 50)
    overlap: int = st.slider("片段重叠（字）", 0, 200, 60, 10)
    enable_rag: bool = st.toggle("启用 RAG 检索增强", value=True)
    show_context: bool = st.toggle("展示检索到的参考资料", value=True)

    st.divider()
    st.header("知识库")
    use_sample: bool = st.checkbox("内置示例文档", value=True)
    uploads = st.file_uploader(
        "上传文档（txt / md / pdf）",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
    )
    manual_text: str = st.text_area("或粘贴文本", height=120, placeholder="在此粘贴要入库的知识文本……")

    if st.button("构建 / 重建知识库", type="primary", use_container_width=True):
        build_kb(use_sample, uploads, manual_text, embed_model, chunk_size, overlap)

    kb: KnowledgeBase | None = st.session_state.kb
    if kb is None:
        st.info("尚未构建知识库")
    else:
        st.success(f"知识库已就绪：{kb.size} 个片段 ｜ 向量模型 {kb.embed_model}")
        if st.button("清空知识库", use_container_width=True):
            st.session_state.kb = None
            st.rerun()

    return {
        "chat_model": chat_model,
        "embed_model": embed_model,
        "temperature": temperature,
        "top_k": top_k,
        "enable_rag": enable_rag,
        "show_context": show_context,
    }


def build_kb(
    use_sample: bool,
    uploads: list[Any],
    manual_text: str,
    embed_model: str,
    chunk_size: int,
    overlap: int,
) -> None:
    """收集资料、切分、向量化，并把结果写入会话状态。"""
    docs: dict[str, str] = {}
    if use_sample:
        docs.update(SAMPLE_DOCS)
    for upload in uploads:
        docs[upload.name] = read_uploaded_file(upload.name, upload.getvalue())
    if manual_text.strip():
        docs["粘贴文本"] = manual_text.strip()

    if not docs:
        st.error("请至少选择一种资料来源（示例文档 / 上传文件 / 粘贴文本）")
        return

    progress = st.progress(0.0, text="正在向量化……")
    status = st.empty()

    def on_progress(done: int, total: int) -> None:
        """向量化进度回调。"""
        progress.progress(done / total, text=f"正在向量化 {done}/{total}……")
        status.caption(f"已处理 {done}/{total} 个片段")

    try:
        kb: KnowledgeBase = build_knowledge_base(
            CLIENT, docs, embed_model, chunk_size, overlap, on_progress
        )
    except Exception as exc:  # 网络 / 鉴权 / 模型名错误都在这里集中提示
        progress.empty()
        status.empty()
        st.error(f"构建知识库失败：{exc}")
        return

    progress.empty()
    status.empty()
    st.session_state.kb = kb
    st.session_state.messages = []
    st.success(f"知识库构建完成，共 {kb.size} 个片段")


def render_hits(hits: list[Hit]) -> None:
    """把检索到的片段渲染成可展开的详情。"""
    with st.expander(f"检索到的参考资料（{len(hits)} 条）", expanded=True):
        for number, hit in enumerate(hits, start=1):
            chunk: Chunk = hit.chunk
            st.markdown(
                f"**[{number}] {chunk.source}** ｜ 片段 #{chunk.index} ｜ "
                f"相似度 `{hit.score:.3f}`"
            )
            st.caption(chunk.text)


def render_history() -> None:
    """渲染已有对话。"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def answer(params: dict[str, Any], query: str) -> None:
    """执行一次问答：检索 -> 组装提示词 -> 流式生成 -> 渲染。"""
    kb: KnowledgeBase | None = st.session_state.kb
    enable_rag: bool = bool(params["enable_rag"]) and kb is not None
    hits: list[Hit] = []

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        if enable_rag and kb is not None:
            with st.spinner("正在检索……"):
                hits = search(CLIENT, kb, query, int(params["top_k"]))
            if params["show_context"]:
                render_hits(hits)
        elif kb is None:
            st.caption("未构建知识库，本次为纯大模型回答")

        messages = build_messages(
            query, hits, st.session_state.messages, enable_rag
        )
        try:
            answer_text: str = st.write_stream(
                stream_answer(
                    CLIENT,
                    str(params["chat_model"]),
                    messages,
                    float(params["temperature"]),
                )
            )
        except Exception as exc:
            st.error(f"生成失败：{exc}")
            return

    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.messages.append({"role": "assistant", "content": answer_text})


def main() -> None:
    """页面主流程。"""
    init_state()
    st.title("RAG 大模型问答 Demo")
    st.caption("上传文档 → 切分向量化 → 相似度检索 → 大模型基于参考资料作答")

    with st.sidebar:
        params = render_sidebar()

    render_history()

    query: str | None = st.chat_input("请输入问题……")
    if query:
        answer(params, query)


if __name__ == "__main__":
    main()
