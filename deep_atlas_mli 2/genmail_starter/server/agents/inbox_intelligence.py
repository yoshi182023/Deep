# =============================================================================
# 第九步：主动收件箱提醒（功能 9）— 【LangGraph】
# -----------------------------------------------------------------------------
# 全项目 LangGraph 模块之一（另见 draft_reply.py 功能 8、cross_thread.py 功能 10）。
#
# 图结构：
#   START ──fan-out(Send×3)──► gather_needs / gather_commitments / gather_stalled
#         ──(并行汇合)──► human_review【interrupt 确认待办】► build_report ──► END
#
# API：
#   start_proactive_inbox()  → graph.invoke()，interrupt 处返回 run_id + 待确认列表
#   resume_proactive_inbox() → Command(resume) 确认后生成报告
# =============================================================================
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from agents.client import chat_completion
from agents.commitments import extract_commitments, gather_sent_emails
from agents.thread_state import gather_thread_state_facts
from models import Email, db

PRIMARY_USER = "pm@acme.com"

REPORT_PROMPT = """你是收件箱智能助手。根据用户确认的待办线索，生成「收件箱智能（主动）」报告。

格式必须包含三个板块（无内容则写「无」）：
🔴 需要你回复（N）：
⏳ 到期承诺（N）：
⚠️ 停滞对话（N）：

每项包含：发件人/对象、主题摘要、原因（why）。
使用中文，简洁编号列表，不要编造线索中没有的邮件。"""


class ProactiveInboxState(TypedDict, total=False):
    """【LangGraph 状态】并行 gather 写入各列表，确认后 build_report 生成 report"""
    needs_response: list
    commitments_due: list
    stalled_conversations: list
    confirmed_items: dict
    report: str
    status: str


_checkpointer = MemorySaver()
_compiled_graph = None


def _display_name(email_address: str) -> str:
    local = email_address.split("@")[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    return " ".join(p.capitalize() for p in parts)


def _iter_threads() -> list[tuple[str, list[Email]]]:
    thread_ids = [row[0] for row in db.session.query(Email.thread_id).distinct().all()]
    result = []
    for thread_id in thread_ids:
        emails = (
            Email.query.filter_by(thread_id=thread_id)
            .order_by(Email.created_at.asc())
            .all()
        )
        if emails:
            result.append((thread_id, emails))
    return result


def gather_needs_response() -> list[dict]:
    """待回复：最后一封是别人发给 pm，且 pm 尚未回复"""
    items = []
    for thread_id, emails in _iter_threads():
        facts = gather_thread_state_facts(thread_id, emails)
        last = emails[-1]
        if last.recipient != PRIMARY_USER or last.sender == PRIMARY_USER:
            continue
        if facts["user_replied_after_last_inbound"]:
            continue

        hours = round((datetime.now() - last.created_at).total_seconds() / 3600, 1)
        items.append(
            {
                "thread_id": thread_id,
                "email_id": last.id,
                "sender": last.sender,
                "sender_name": _display_name(last.sender),
                "subject": facts["subject"],
                "sent_at": last.created_at.isoformat(),
                "hours_since_sent": hours,
                "is_unread": not last.is_read,
                "has_question": facts["last_message_has_question"],
                "subject_urgent": "urgent" in last.subject.lower(),
                "snippet": last.body[:200].replace("\n", " "),
            }
        )

    items.sort(
        key=lambda x: (
            -int(x["is_unread"]),
            -int(x["subject_urgent"]),
            -int(x["has_question"]),
            -x["hours_since_sent"],
        )
    )
    return items


def gather_stalled_conversations(min_days: float = 7) -> list[dict]:
    """停滞对话：他人曾承诺交付，且线程已久无进展"""
    items = []
    for thread_id, emails in _iter_threads():
        facts = gather_thread_state_facts(thread_id, emails)
        promises = facts["pending_promises_from_others"]
        if not promises:
            continue
        days = facts["days_since_last_activity"]
        if days < min_days:
            continue

        last_promise = promises[-1]
        items.append(
            {
                "thread_id": thread_id,
                "subject": facts["subject"],
                "blocking_party": last_promise["from"],
                "blocking_party_name": last_promise["from_name"],
                "days_since_last_activity": days,
                "promise_snippet": last_promise["snippet"],
                "promise_sent_at": last_promise["sent_at"],
            }
        )

    items.sort(key=lambda x: -x["days_since_last_activity"])
    return items


def gather_commitments_due() -> list[dict]:
    """到期或即将到期的承诺（复用功能 5 提取逻辑）"""
    commitments = extract_commitments(gather_sent_emails())
    return [c for c in commitments if c.get("status") in ("due_soon", "overdue")]


# ---------- 【LangGraph 节点】----------


def _gather_all_node(_state: ProactiveInboxState) -> ProactiveInboxState:
    """
    【LangGraph 节点】顺序执行三路 gather。
    注：不用 Send 并行，避免 Flask debug 热重载时 LangGraph 线程池报
    RuntimeError: cannot schedule new futures after shutdown
    """
    return {
        "needs_response": gather_needs_response(),
        "commitments_due": gather_commitments_due(),
        "stalled_conversations": gather_stalled_conversations(),
    }


def _human_review_node(state: ProactiveInboxState) -> ProactiveInboxState:
    """
    【LangGraph interrupt 节点】展示待办列表，等待用户 confirm_all / skip / filtered_items
    """
    needs = state.get("needs_response") or []
    commitments = state.get("commitments_due") or []
    stalled = state.get("stalled_conversations") or []

    # 【LangGraph API】首次 invoke 在此暂停；resume 时 decision 为用户传入的 JSON
    decision = interrupt(
        {
            "needs_response": needs,
            "commitments_due": commitments,
            "stalled_conversations": stalled,
            "needs_response_count": len(needs),
            "commitments_due_count": len(commitments),
            "stalled_count": len(stalled),
            "instruction": "请确认待办项：confirm_all 全部纳入报告，skip 跳过，或传 filtered_items",
        }
    )

    action = decision.get("action", "confirm_all")
    if action == "skip":
        empty = {
            "needs_response": [],
            "commitments_due": [],
            "stalled_conversations": [],
        }
        return {
            "confirmed_items": empty,
            "status": "skipped",
            "report": "收件箱智能（主动）：\n\n已跳过待办确认，未生成报告。",
        }

    if decision.get("filtered_items"):
        confirmed = decision["filtered_items"]
    else:
        confirmed = {
            "needs_response": needs,
            "commitments_due": commitments,
            "stalled_conversations": stalled,
        }

    return {"confirmed_items": confirmed, "status": "confirmed"}


def _build_report_node(state: ProactiveInboxState) -> ProactiveInboxState:
    """【LangGraph 节点】根据用户确认的线索生成 LLM 报告"""
    if state.get("status") == "skipped" and state.get("report"):
        return {}

    items = state.get("confirmed_items") or {
        "needs_response": state.get("needs_response") or [],
        "commitments_due": state.get("commitments_due") or [],
        "stalled_conversations": state.get("stalled_conversations") or [],
    }

    report = chat_completion(
        [
            {"role": "system", "content": REPORT_PROMPT},
            {
                "role": "user",
                "content": (
                    f"当前日期：{datetime.now().date().isoformat()}\n\n"
                    f"已确认线索：\n{json.dumps(items, ensure_ascii=False, indent=2)}"
                ),
            },
        ]
    )
    return {"report": report.strip(), "status": "complete"}


def _build_graph():
    """【LangGraph】gather_all → human_review(interrupt) → build_report"""
    graph = StateGraph(ProactiveInboxState)

    graph.add_node("gather_all", _gather_all_node)
    graph.add_node("human_review", _human_review_node)
    graph.add_node("build_report", _build_report_node)

    graph.add_edge(START, "gather_all")
    graph.add_edge("gather_all", "human_review")
    graph.add_edge("human_review", "build_report")
    graph.add_edge("build_report", END)

    return graph.compile(checkpointer=_checkpointer)


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


def _graph_config(run_id: str) -> dict:
    return {"configurable": {"thread_id": run_id}}


def _require_interrupt_checkpoint(run_id: str) -> None:
    """resume 前校验 checkpoint 仍在 human_review 等待中（防止服务重启后 run_id 失效）"""
    graph = _get_graph()
    snapshot = graph.get_state(_graph_config(run_id))
    if not snapshot.next:
        raise ValueError("会话已过期（可能服务已重启），请刷新页面重新分析")


def _response_from_state(run_id: str, state: dict, *, awaiting: bool = False) -> dict:
    needs = state.get("needs_response") or []
    commitments = state.get("commitments_due") or []
    stalled = state.get("stalled_conversations") or []
    base = {
        "run_id": run_id,
        "needs_response_count": len(needs),
        "commitments_due_count": len(commitments),
        "stalled_count": len(stalled),
        "needs_response": needs,
        "commitments_due": commitments,
        "stalled_conversations": stalled,
    }
    if awaiting:
        base["status"] = "awaiting_confirmation"
        return base
    base["status"] = state.get("status", "complete")
    base["report"] = state.get("report", "")
    return base


def start_proactive_inbox() -> dict:
    """【LangGraph 入口 1】并行 gather 后在 human_review interrupt 暂停"""
    run_id = str(uuid.uuid4())
    graph = _get_graph()
    result = graph.invoke({}, _graph_config(run_id))

    if "__interrupt__" not in result:
        raise ValueError("收件箱智能流程未在确认节点暂停")

    payload = result["__interrupt__"][0].value
    merged = {**result, **payload}
    return _response_from_state(run_id, merged, awaiting=True)


def resume_proactive_inbox(
    run_id: str,
    action: Literal["confirm_all", "skip"] = "confirm_all",
    filtered_items: dict | None = None,
) -> dict:
    """【LangGraph 入口 2】Command(resume) 确认待办后继续 build_report"""
    _require_interrupt_checkpoint(run_id)

    resume_payload: dict = {"action": action}
    if filtered_items is not None:
        resume_payload["filtered_items"] = filtered_items

    graph = _get_graph()
    result = graph.invoke(Command(resume=resume_payload), _graph_config(run_id))

    if result.get("status") not in ("complete", "skipped"):
        raise ValueError("报告生成未完成，请刷新后重试")
    if result.get("status") == "complete" and not result.get("report"):
        raise ValueError("报告生成失败，请刷新后重试")

    return _response_from_state(run_id, result, awaiting=False)


def proactive_inbox() -> dict:
    """兼容旧调用：自动 confirm_all 一键跑完（无前端 HITL 时使用）"""
    started = start_proactive_inbox()
    return resume_proactive_inbox(started["run_id"], action="confirm_all")
