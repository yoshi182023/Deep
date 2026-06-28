"""Minimal chatbot app built on existing RAG pipeline logic."""

import atexit
import os
from typing import List, Dict

import gradio as gr
from dotenv import load_dotenv

from answer_generation import MockRAGPipeline, RAGPipeline


ROOT_ENV = "/workspaces/Deep/.env"
_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    load_dotenv(ROOT_ENV)
    connection_url = os.getenv("NEON_PG_CONNECTION_URL")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    if not connection_url:
        raise RuntimeError("Missing NEON_PG_CONNECTION_URL in .env")

    use_mock = not gemini_api_key or gemini_api_key == "your_gemini_api_key_here"

    if use_mock:
        _pipeline = MockRAGPipeline(connection_url, top_k=5)
    else:
        try:
            _pipeline = RAGPipeline(
                connection_url=connection_url,
                gemini_api_key=gemini_api_key,
                model="gemini-2.0-flash",
                top_k=5,
            )
        except Exception:
            _pipeline = MockRAGPipeline(connection_url, top_k=5)

    return _pipeline


def build_source_text(sources):
    if not sources:
        return ""
    source_ids = [s.get("email_id", "unknown") for s in sources[:5]]
    return "\n\n信息来源: " + ", ".join(source_ids)


def normalize_history(history):
    """Convert mixed legacy/new history into messages format for Gradio 6."""
    if not history:
        return []

    normalized = []
    for item in history:
        # New format: {"role": ..., "content": ...}
        if isinstance(item, dict) and "role" in item and "content" in item:
            normalized.append({"role": str(item["role"]), "content": str(item["content"])})
            continue

        # Legacy format: (user, bot) or [user, bot]
        if isinstance(item, (tuple, list)) and len(item) == 2:
            user_msg, bot_msg = item
            normalized.append({"role": "user", "content": str(user_msg)})
            normalized.append({"role": "assistant", "content": str(bot_msg)})
            continue

        # Unknown item type: skip silently
    return normalized


def append_history(history, user_message: str, bot_text: str):
    """Gradio 6 Chatbot expects messages with role/content."""
    base = normalize_history(history)
    return base + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": bot_text},
    ]


def chat(user_message: str, history):
    if not user_message.strip():
        return "", normalize_history(history)

    pipeline = get_pipeline()
    resp = pipeline.ask(user_message)
    bot_text = (resp.answer or "") + build_source_text(resp.sources)

    history = append_history(history, user_message, bot_text)
    return "", history


def clear_chat():
    return [], ""


def on_exit():
    global _pipeline
    if _pipeline is not None:
        try:
            _pipeline.close()
        except Exception:
            pass


atexit.register(on_exit)


with gr.Blocks(title="Email RAG Chatbot") as app:
    gr.Markdown("# Email RAG Chatbot")
    gr.Markdown("基于现有检索 + 语义缓存 + 答案生成逻辑")

    chatbot = gr.Chatbot(height=520)
    user_input = gr.Textbox(
        label="提问",
        placeholder="例如：哪些公司正在招聘工程师？",
    )

    with gr.Row():
        send_btn = gr.Button("发送", variant="primary")
        clear_btn = gr.Button("清空")

    send_btn.click(chat, inputs=[user_input, chatbot], outputs=[user_input, chatbot])
    user_input.submit(chat, inputs=[user_input, chatbot], outputs=[user_input, chatbot])
    clear_btn.click(clear_chat, outputs=[chatbot, user_input])


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
