# =============================================================================
# 第七步：线程状态分类（功能 7）
# -----------------------------------------------------------------------------
# 目标：判断邮件线程当前状态（谁在等谁、是否阻塞、是否已结束）。
#
# 设计思路（与功能 4、6 一致）：
#   1. gather_thread_state_facts() — Python 算客观信号（最后发言人、停滞天数、承诺线索等）
#   2. classify_thread_state()     — LLM 结合线程全文输出 state + context
#
# 不持久化：按需实时计算，供功能 9「停滞对话」复用。
# =============================================================================
import json
import re
from datetime import datetime

from agents.client import chat_completion
from agents.summarizer import format_thread
from models import Email

PRIMARY_USER = "pm@acme.com"

PROMISE_PATTERN = re.compile(
    r"(I'll|I will|我会|我将|tomorrow|明天|by Friday|周五)",
    re.IGNORECASE,
)

STATE_LABELS = {
    "ACTIVE": "讨论进行中",
    "WAITING_ON_YOU": "等待你回复",
    "WAITING_ON_THEM": "等待他人回复",
    "BLOCKED": "阻塞 — 等待外部输入",
    "RESOLVED": "已解决 / 已结束",
    "FYI": "仅供参考，无需操作",
}

CLASSIFY_PROMPT = """你是邮件线程状态分析助手。根据完整对话和系统提供的事实，判断线程当前状态。

可选状态（state 字段必须用英文枚举值）：
- ACTIVE — 讨论仍在进行，有来回但未明确卡在谁身上
- WAITING_ON_YOU — 对方最后一封在等你回复（问题、邀请、请求决策）
- WAITING_ON_THEM — 你最后一封在等对方回复
- BLOCKED — 对方承诺交付某物（文档、决定、资源）但未兑现，导致你无法推进
- RESOLVED — 已有明确结论，对话自然结束
- FYI — 纯信息同步，无需任何操作

判断要点：
- BLOCKED vs WAITING_ON_THEM：对方说「我明天发文档」而你需要该文档才能继续 → BLOCKED
- 沉默结合 days_since_last_activity 判断，不要一律标 RESOLVED
- blocking_party 填阻碍进展的人的邮箱；若无则 null
- context 为 3–5 条中文 bullet，引用对话原文，不要编造

示例：
- Jennifer 说明天发 Globex 需求文档，之后再无消息 → BLOCKED, blocking_party=jennifer
- Sarah 邀你参加 sprint planning，你未回复 → WAITING_ON_YOU
- 你已选定 Option B，决策完成 → RESOLVED

只输出 JSON，不要其他文字。格式：
{{
  "state": "ACTIVE|WAITING_ON_YOU|WAITING_ON_THEM|BLOCKED|RESOLVED|FYI",
  "blocking_party": "邮箱或 null",
  "blocking_party_name": "姓名或 null",
  "context": ["上下文1", "上下文2"]
}}"""


def _display_name(email_address: str) -> str:
    local = email_address.split("@")[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    return " ".join(p.capitalize() for p in parts)


def _find_pending_promises(emails: list[Email]) -> list[dict]:
    """从线程中提取他人做出的交付承诺线索"""
    promises = []
    for email in emails:
        if email.sender == PRIMARY_USER:
            continue
        if not PROMISE_PATTERN.search(email.body):
            continue
        for match in PROMISE_PATTERN.finditer(email.body):
            start = max(0, match.start() - 40)
            end = min(len(email.body), match.end() + 80)
            promises.append(
                {
                    "from": email.sender,
                    "from_name": _display_name(email.sender),
                    "sent_at": email.created_at.isoformat(),
                    "snippet": email.body[start:end].replace("\n", " ").strip(),
                }
            )
            break
    return promises


def gather_thread_state_facts(thread_id: str, emails: list[Email]) -> dict:
    """收集线程状态相关的客观事实（不调用 LLM）"""
    now = datetime.now()
    last = emails[-1]
    first = emails[0]

    days_since_last = round((now - last.created_at).total_seconds() / 86400, 1)
    last_from_user = last.sender == PRIMARY_USER

    last_inbound = None
    for email in reversed(emails):
        if email.recipient == PRIMARY_USER and email.sender != PRIMARY_USER:
            last_inbound = email
            break

    user_replied_after_last_inbound = False
    if last_inbound:
        for email in emails:
            if email.created_at <= last_inbound.created_at:
                continue
            if email.sender == PRIMARY_USER:
                user_replied_after_last_inbound = True
                break

    unread_inbound = sum(
        1
        for e in emails
        if e.recipient == PRIMARY_USER
        and e.sender != PRIMARY_USER
        and not e.is_read
    )

    last_body = last.body
    last_has_question = "?" in last_body or "？" in last_body

    return {
        "thread_id": thread_id,
        "subject": first.subject,
        "message_count": len(emails),
        "participants": sorted(
            {e.sender for e in emails} | {e.recipient for e in emails}
        ),
        "last_sender": last.sender,
        "last_recipient": last.recipient,
        "last_sender_name": _display_name(last.sender),
        "last_message_from_user": last_from_user,
        "last_activity_at": last.created_at.isoformat(),
        "days_since_last_activity": days_since_last,
        "last_inbound_from": last_inbound.sender if last_inbound else None,
        "last_inbound_at": last_inbound.created_at.isoformat() if last_inbound else None,
        "user_replied_after_last_inbound": user_replied_after_last_inbound,
        "unread_inbound_count": unread_inbound,
        "last_message_has_question": last_has_question,
        "pending_promises_from_others": _find_pending_promises(emails),
    }


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def classify_thread_state(thread_id: str) -> dict | None:
    """
    功能 7 入口：分析线程当前状态。
    返回 None 表示线程不存在。
    """
    emails = (
        Email.query.filter_by(thread_id=thread_id)
        .order_by(Email.created_at.asc())
        .all()
    )
    if not emails:
        return None

    facts = gather_thread_state_facts(thread_id, emails)

    raw = chat_completion(
        [
            {"role": "system", "content": CLASSIFY_PROMPT},
            {
                "role": "user",
                "content": (
                    f"当前日期：{datetime.now().date().isoformat()}\n\n"
                    f"线程 ID：{thread_id}\n\n"
                    f"客观事实（facts）：\n"
                    f"{json.dumps(facts, ensure_ascii=False, indent=2)}\n\n"
                    f"完整对话：\n{format_thread(emails)}"
                ),
            },
        ]
    )

    try:
        result = _parse_json_response(raw)
    except json.JSONDecodeError:
        result = {
            "state": "ACTIVE",
            "blocking_party": None,
            "blocking_party_name": None,
            "context": ["LLM 返回格式异常，已使用默认状态 ACTIVE。"],
        }

    state = result.get("state", "ACTIVE")
    blocking_party = result.get("blocking_party")
    blocking_name = result.get("blocking_party_name")
    if blocking_party and not blocking_name:
        blocking_name = _display_name(blocking_party)

    return {
        "thread_id": thread_id,
        "subject": facts["subject"],
        "message_count": facts["message_count"],
        "state": state,
        "state_label": STATE_LABELS.get(state, state),
        "blocking_party": blocking_party,
        "blocking_party_name": blocking_name,
        "last_activity_at": facts["last_activity_at"],
        "days_since_last_activity": facts["days_since_last_activity"],
        "context": result.get("context", []),
        "facts": facts,
    }
