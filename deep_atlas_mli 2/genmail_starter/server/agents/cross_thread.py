# =============================================================================
# 第十步：跨线程综合（功能 10）— 【LangGraph】
# -----------------------------------------------------------------------------
# 图结构：
#   START → search【SQL 搜主题】→ synthesize【LLM 初稿】→ reflect【LLM 自检补漏】→ END
#
# reflect 节点对照原始线程检查遗漏、矛盾，输出终稿 report。
# =============================================================================
from __future__ import annotations

from collections import defaultdict
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agents.client import chat_completion
from agents.summarizer import format_thread
from models import Email

SYNTHESIS_PROMPT = """你是邮件跨线程综合分析助手。用户给定一个主题关键词，请综合所有相关线程中的信息。

报告须包含以下板块（中文）：
- 时间表
- 关键决策
- 阻碍
- 相关人员

要求：
- 只使用提供的邮件内容，不要编造
- 标注信息来源（发件人、大致日期）
- 使用 bullet 列表，结构清晰"""

REFLECT_PROMPT = """你是邮件综合分析质检助手。请对照原始线程内容，审阅并改进下面的跨线程综合初稿。

检查：
1. 是否遗漏重要线程或关键决策
2. 是否有与邮件矛盾或已过时的信息
3. 结构是否清晰（时间表、关键决策、阻碍、相关人员）

输出改进后的最终报告（中文）。若初稿已足够好，可微调措辞后返回。不要编造原始邮件中没有的内容。"""


class SynthesisState(TypedDict, total=False):
    """【LangGraph 状态】search → synthesize → reflect"""
    topic: str
    email_count: int
    thread_count: int
    thread_ids: list[str]
    thread_blocks: str
    draft_report: str
    report: str
    status: str


_compiled_graph = None


def find_topic_emails(topic: str) -> list[Email]:
    """在主题和正文中搜索关键词（不区分大小写）"""
    topic = topic.strip()
    if not topic:
        return []

    pattern = f"%{topic}%"
    return (
        Email.query.filter(
            (Email.subject.ilike(pattern)) | (Email.body.ilike(pattern))
        )
        .order_by(Email.created_at.asc())
        .all()
    )


def _search_node(state: SynthesisState) -> SynthesisState:
    """【LangGraph 节点 1】SQL 搜索并按线程分组"""
    topic = state["topic"].strip()
    emails = find_topic_emails(topic)

    if not emails:
        return {
            "email_count": 0,
            "thread_count": 0,
            "thread_ids": [],
            "thread_blocks": "",
            "status": "empty",
            "draft_report": f"未找到与「{topic}」相关的邮件。",
            "report": f"未找到与「{topic}」相关的邮件。",
        }

    by_thread: dict[str, list[Email]] = defaultdict(list)
    for email in emails:
        by_thread[email.thread_id].append(email)

    thread_blocks = []
    for thread_id, thread_emails in by_thread.items():
        thread_emails.sort(key=lambda e: e.created_at)
        thread_blocks.append(
            f"=== 线程 {thread_id}（{thread_emails[0].subject}）===\n"
            f"{format_thread(thread_emails)}"
        )

    return {
        "email_count": len(emails),
        "thread_count": len(by_thread),
        "thread_ids": list(by_thread.keys()),
        "thread_blocks": "\n\n".join(thread_blocks),
        "status": "searched",
    }


def _synthesize_node(state: SynthesisState) -> SynthesisState:
    """【LangGraph 节点 2】LLM 生成综合初稿"""
    if state.get("status") == "empty":
        return {}

    topic = state["topic"]
    draft = chat_completion(
        [
            {"role": "system", "content": SYNTHESIS_PROMPT},
            {
                "role": "user",
                "content": (
                    f"主题关键词：{topic}\n"
                    f"匹配 {state['email_count']} 封邮件，{state['thread_count']} 个线程。\n\n"
                    f"{state['thread_blocks']}"
                ),
            },
        ]
    )
    return {"draft_report": draft.strip(), "status": "drafted"}


def _reflect_node(state: SynthesisState) -> SynthesisState:
    """【LangGraph 节点 3 — 自检】对照原始线程改进初稿，输出终稿"""
    if state.get("status") == "empty":
        return {}

    final = chat_completion(
        [
            {"role": "system", "content": REFLECT_PROMPT},
            {
                "role": "user",
                "content": (
                    f"主题：{state['topic']}\n\n"
                    f"原始线程：\n{state['thread_blocks']}\n\n"
                    f"综合初稿：\n{state['draft_report']}\n\n"
                    "请输出最终报告："
                ),
            },
        ]
    )
    return {"report": final.strip(), "status": "complete"}


def _build_graph():
    """【LangGraph】search → synthesize → reflect 线性三节点"""
    graph = StateGraph(SynthesisState)
    graph.add_node("search", _search_node)
    graph.add_node("synthesize", _synthesize_node)
    graph.add_node("reflect", _reflect_node)

    graph.add_edge(START, "search")
    graph.add_edge("search", "synthesize")
    graph.add_edge("synthesize", "reflect")
    graph.add_edge("reflect", END)

    return graph.compile()


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


def synthesize_topic(topic: str) -> dict:
    """
    【LangGraph 入口】一次 invoke 跑完 search → synthesize → reflect。
    """
    topic = topic.strip()
    if not topic:
        raise ValueError("主题不能为空")

    result = _get_graph().invoke({"topic": topic})

    return {
        "topic": topic,
        "email_count": result.get("email_count", 0),
        "thread_count": result.get("thread_count", 0),
        "thread_ids": result.get("thread_ids", []),
        "draft_report": result.get("draft_report"),
        "report": result.get("report", ""),
    }
