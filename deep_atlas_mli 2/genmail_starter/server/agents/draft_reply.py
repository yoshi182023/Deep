# =============================================================================
# 第八步：智能回复起草（功能 8）— LangGraph + Human-in-the-Loop
# -----------------------------------------------------------------------------
# 【本项目唯一使用 LangGraph 的模块】其余功能 1–7、9–10 均为手写 Python + chat_completion。
#
# LangGraph 负责：
#   - StateGraph：把「加载上下文 → 生成草稿 → 人工审批 → 发送」串成有状态工作流
#   - MemorySaver：保存每次 run 的 checkpoint，支持 interrupt 后 resume
#   - interrupt()：在 human_review 节点暂停，等待用户 approve / edit / reject
#   - Command(resume=...)：用户审批后从断点继续执行图
#
# 流程节点：
#   1. load_context   — 普通 Python（非 LangGraph 专有 API）
#   2. generate_draft — 普通 LLM 调用
#   3. human_review   — 【LangGraph interrupt 节点】
#   4. send_email     — 普通 Python 写库
#
# API：
#   POST /ai/draft-reply/<thread_id>  → graph.invoke() 启动，在 interrupt 处返回
#   POST /ai/draft-reply/resume       → graph.invoke(Command(resume=...)) 继续
# =============================================================================
from __future__ import annotations

import uuid
from typing import Literal, TypedDict

# ---------- LangGraph 依赖（仅本文件使用）----------
from langgraph.checkpoint.memory import MemorySaver  # 内存 checkpoint，保存 interrupt 前的图状态
from langgraph.graph import END, START, StateGraph  # 状态图：节点 + 边
from langgraph.types import Command, interrupt  # interrupt=人工暂停；Command=resume 续跑

from agents.client import chat_completion
from agents.summarizer import format_thread
from models import Email, db

PRIMARY_USER = "pm@acme.com"

DRAFT_SYSTEM_PROMPT = """你是Alex（pm@acme.com）的邮件写作助手。
根据线程对话起草一封自然、专业的回复。

要求：
- 回答对方最新邮件中的问题或请求
- 引用线程中的关键上下文，不要重复已说过的内容
- 不要编造线程中没有的事实
- 正文用英文（与种子邮件一致），落款 Alex
- 只输出邮件正文，不要主题行，不要 JSON"""


class DraftReplyState(TypedDict, total=False):
    """LangGraph 图的全局状态：各节点读写此 dict，checkpoint 会持久化它"""
    thread_id: str
    recipient: str
    recipient_name: str
    subject: str
    draft_body: str
    human_decision: str | None
    final_body: str | None
    sent: bool
    email_id: int | None
    status: str


# LangGraph 检查点存储器：key 为 run_id（见 _graph_config），用于 interrupt 后恢复
_checkpointer = MemorySaver()
# 编译后的 LangGraph 应用（单例，避免重复 compile）
_compiled_graph = None


def _display_name(email_address: str) -> str:
    local = email_address.split("@")[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    return " ".join(p.capitalize() for p in parts)


def _reply_target(emails: list[Email]) -> str:
    """确定回复对象：回复线程中最新一封的对方"""
    latest = emails[-1]
    if latest.sender == PRIMARY_USER:
        return latest.recipient
    return latest.sender


def _reply_subject(emails: list[Email]) -> str:
    base = emails[0].subject
    if base.lower().startswith("re:"):
        return base
    return f"Re: {base}"


def _past_outbound_to(contact: str, limit: int = 5) -> list[Email]:
    return (
        Email.query.filter_by(sender=PRIMARY_USER, recipient=contact)
        .order_by(Email.created_at.desc())
        .limit(limit)
        .all()
    )


def _format_past_style(emails: list[Email]) -> str:
    if not emails:
        return "（无历史往来）"
    blocks = []
    for email in reversed(emails):
        blocks.append(f"Subject: {email.subject}\n{email.body}")
    return "\n\n---\n\n".join(blocks)


def _load_context_node(state: DraftReplyState) -> DraftReplyState:
    """【LangGraph 节点 1】加载线程元数据，写入图状态"""
    thread_id = state["thread_id"]
    emails = (
        Email.query.filter_by(thread_id=thread_id)
        .order_by(Email.created_at.asc())
        .all()
    )
    if not emails:
        raise ValueError(f"线程不存在: {thread_id}")

    recipient = _reply_target(emails)
    return {
        "recipient": recipient,
        "recipient_name": _display_name(recipient),
        "subject": _reply_subject(emails),
        "status": "generating",
    }


def _generate_draft_node(state: DraftReplyState) -> DraftReplyState:
    """【LangGraph 节点 2】LLM 生成草稿（本节点内不用 LangGraph API，只是图中的一步）"""
    thread_id = state["thread_id"]
    emails = (
        Email.query.filter_by(thread_id=thread_id)
        .order_by(Email.created_at.asc())
        .all()
    )
    recipient = state["recipient"]
    past = _past_outbound_to(recipient)

    draft = chat_completion(
        [
            {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"收件人：{state['recipient_name']} ({recipient})\n"
                    f"回复主题：{state['subject']}\n\n"
                    f"当前线程：\n{format_thread(emails)}\n\n"
                    f"Alex 过往发给 {state['recipient_name']} 的邮件（语气参考）：\n"
                    f"{_format_past_style(past)}\n\n"
                    "请起草回复正文："
                ),
            },
        ]
    )

    return {
        "draft_body": draft.strip(),
        "status": "awaiting_approval",
    }


def _human_review_node(state: DraftReplyState) -> DraftReplyState:
    """
    【LangGraph 节点 3 — Human-in-the-Loop 核心】
    调用 interrupt() 后图会暂停，invoke() 返回 __interrupt__；
    用户通过 resume API 传入 decision 后，从此处继续执行。
    """
    # 【LangGraph API】抛出中断，把草稿交给前端审批；resume 时 decision 为 resume 传入的 JSON
    decision = interrupt(
        {
            "thread_id": state["thread_id"],
            "recipient": state["recipient"],
            "recipient_name": state["recipient_name"],
            "subject": state["subject"],
            "draft_body": state["draft_body"],
            "instruction": "请审阅草稿：approve 发送，edit 发送修改后的正文，reject 取消",
        }
    )

    action = decision.get("action", "approve")
    if action == "reject":
        return {
            "human_decision": "reject",
            "final_body": None,
            "status": "rejected",
        }

    body = (decision.get("body") or state["draft_body"]).strip()
    return {
        "human_decision": action,
        "final_body": body,
    }


def _send_email_node(state: DraftReplyState) -> DraftReplyState:
    """【LangGraph 节点 4】审批通过后写库；reject 时仅更新状态不发信"""
    if state.get("human_decision") == "reject":
        return {"sent": False, "status": "rejected"}

    body = state.get("final_body") or state.get("draft_body", "")
    email = Email(
        thread_id=state["thread_id"],
        sender=PRIMARY_USER,
        recipient=state["recipient"],
        subject=state["subject"],
        body=body,
    )
    db.session.add(email)
    db.session.commit()

    return {
        "sent": True,
        "email_id": email.id,
        "status": "sent",
    }


def _build_graph():
    """【LangGraph】构建并 compile 状态图：START → … → END，并挂上 MemorySaver"""
    graph = StateGraph(DraftReplyState)
    # 注册四个节点（每个函数对应图上的一个 step）
    graph.add_node("load_context", _load_context_node)
    graph.add_node("generate_draft", _generate_draft_node)
    graph.add_node("human_review", _human_review_node)
    graph.add_node("send_email", _send_email_node)

    # 定义边的执行顺序（固定流水线，无循环）
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "generate_draft")
    graph.add_edge("generate_draft", "human_review")
    graph.add_edge("human_review", "send_email")
    graph.add_edge("send_email", END)

    # compile：生成可 invoke 的 Runnable，checkpointer 使 interrupt/resume 成为可能
    return graph.compile(checkpointer=_checkpointer)


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


def _graph_config(run_id: str) -> dict:
    """LangGraph 运行配置：thread_id 即 checkpoint 键，与前端持有的 run_id 一致"""
    return {"configurable": {"thread_id": run_id}}


def _require_interrupt_checkpoint(run_id: str) -> None:
    """resume 前校验 checkpoint 仍在等待审批（服务重启后 run_id 会失效）"""
    graph = _get_graph()
    snapshot = graph.get_state(_graph_config(run_id))
    if not snapshot.next:
        raise ValueError("会话已过期（可能服务已重启），请重新生成草稿")


def start_draft_reply(thread_id: str) -> dict:
    """
    【LangGraph 入口 1】graph.invoke(initial_state) 跑到 interrupt 为止。
    返回 run_id 供 resume；草稿从 result['__interrupt__'] 取出。
    """
    emails = Email.query.filter_by(thread_id=thread_id).first()
    if emails is None:
        return None

    run_id = str(uuid.uuid4())
    graph = _get_graph()
    initial: DraftReplyState = {
        "thread_id": thread_id,
        "draft_body": "",
        "human_decision": None,
        "final_body": None,
        "sent": False,
        "email_id": None,
        "status": "started",
    }

    # 【LangGraph API】首次 invoke：执行 load_context → generate_draft → interrupt
    result = graph.invoke(initial, _graph_config(run_id))

    # interrupt 后 LangGraph 在返回值里附带 __interrupt__ 列表
    if "__interrupt__" not in result:
        raise ValueError("草稿流程未在审批节点暂停")

    payload = result["__interrupt__"][0].value

    return {
        "run_id": run_id,
        "status": "awaiting_approval",
        "thread_id": thread_id,
        "recipient": payload["recipient"],
        "recipient_name": payload["recipient_name"],
        "subject": payload["subject"],
        "draft_body": payload["draft_body"],
    }


def resume_draft_reply(
    run_id: str,
    action: Literal["approve", "edit", "reject"],
    body: str | None = None,
) -> dict:
    """
    【LangGraph 入口 2】Command(resume=...) 从 human_review 断点继续 → send_email。
    """
    if action not in ("approve", "edit", "reject"):
        raise ValueError("action 必须是 approve、edit 或 reject")
    if action == "edit" and not body:
        raise ValueError("edit 需要提供 body")

    _require_interrupt_checkpoint(run_id)

    graph = _get_graph()
    resume_payload: dict = {"action": action}
    if body is not None:
        resume_payload["body"] = body

    # 【LangGraph API】resume 把用户审批结果传回 human_review 节点内的 interrupt()
    result = graph.invoke(Command(resume=resume_payload), _graph_config(run_id))

    if result.get("status") == "rejected":
        return {
            "run_id": run_id,
            "status": "rejected",
            "sent": False,
        }

    if result.get("sent"):
        email = Email.query.get(result["email_id"])
        return {
            "run_id": run_id,
            "status": "sent",
            "sent": True,
            "email": email.to_dict() if email else None,
        }

    raise ValueError("草稿流程状态异常，请重新生成")
