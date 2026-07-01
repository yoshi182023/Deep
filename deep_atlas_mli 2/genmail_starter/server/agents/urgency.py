# =============================================================================
# 第六步：紧急程度分类（功能 6）
# -----------------------------------------------------------------------------
# 目标：对单封邮件打 1–10 紧急分，并给出中文推理。
#
# 设计思路（两步走，与功能 4 一致）：
#   1. gather_urgency_facts()   — Python 从 DB 算客观信号（时间、已读、是否已回复等）
#   2. classify_email_urgency() — 把事实 + 邮件正文交给 LLM，输出 JSON 分数与推理
#
# 不持久化：每次按需计算，避免分数过期与缓存失效逻辑。
# =============================================================================
import json
import re
from datetime import datetime

from agents.client import chat_completion
from models import Email

PRIMARY_USER = "pm@acme.com"

URGENT_KEYWORDS = ("urgent", "asap", "immediately", "critical", "emergency", "need decision")

CLASSIFY_PROMPT = """你是邮件紧急程度分析助手。根据邮件内容、发件人背景和系统提供的事实，评估该邮件的紧急程度。

评分标准（1–10）——评估邮件本身的紧急性（内容、发件人、客户影响），不要因为「已过很久」或「用户已回复」而降低 score：
- 9–10：客户故障、生产问题、明确升级、关键决策截止
- 6–8：需要尽快回复的决策/问题、重要干系人直接询问
- 3–5：一般工作邮件、信息同步、可稍后处理
- 1–2：周报、感谢信、无行动要求的通知

action_needed 单独判断：若 facts 中 user_replied_after 为 true，则 action_needed 应为 false；否则根据是否仍需 pm 回复判断。

score 与 action_needed 完全独立：已回复的邮件仍可以是 9/10 高分。例如：
- 「URGENT: 客户 Initech 数据同步故障」+ Mike 很少升级 + 用户 17 分钟内回复 → score: 9, level: high, action_needed: false

注意：
- 主题含 URGENT 不一定是真紧急，需结合正文与发件人习惯（sender_recent_subjects）判断
- 若 user_reply_minutes 很短（如 <30 分钟），可作为「邮件确实紧急」的推理依据写入 reasoning
- 不要因 hours_since_sent 很大就把 score 降到很低；历史邮件仍应按内容评估紧急程度
- reasoning 用中文 bullet，引用 facts 中的数据，不要编造
- false_alarm_risk: low | medium | high

只输出 JSON，不要其他文字。格式：
{{
  "score": 1-10,
  "level": "low|medium|high",
  "action_needed": true/false,
  "reasoning": ["推理1", "推理2"],
  "false_alarm_risk": "low|medium|high"
}}"""


def _display_name(email_address: str) -> str:
    local = email_address.split("@")[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    return " ".join(p.capitalize() for p in parts)


def _subject_flags(subject: str) -> list[str]:
    """主题行关键词命中（小写匹配）"""
    lower = subject.lower()
    return [kw for kw in URGENT_KEYWORDS if kw in lower]


def _extract_entity_tokens(text: str) -> list[str]:
    """从正文/主题提取可能出现在其他线程的实体（公司名、产品名等）"""
    candidates = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    stop = {
        "Alex", "Thanks", "Re", "Hi", "Hello", "Dear", "Friday", "Thursday",
        "January", "They", "This", "That", "Data", "Sarah", "Mike", "Lisa",
    }
    tokens = []
    for word in candidates:
        if word in stop or len(word) < 4:
            continue
        if word not in tokens:
            tokens.append(word)
    return tokens[:6]


def _cross_thread_mentions(email: Email, tokens: list[str]) -> list[dict]:
    """在其他线程中搜索相同实体提及，提供跨线程上下文"""
    if not tokens:
        return []

    mentions: list[dict] = []
    seen_threads: set[str] = {email.thread_id}

    for token in tokens:
        pattern = f"%{token}%"
        rows = (
            Email.query.filter(Email.id != email.id)
            .filter(
                (Email.subject.ilike(pattern)) | (Email.body.ilike(pattern))
            )
            .order_by(Email.created_at.desc())
            .limit(20)
            .all()
        )
        for row in rows:
            if row.thread_id in seen_threads:
                continue
            seen_threads.add(row.thread_id)
            mentions.append(
                {
                    "entity": token,
                    "thread_id": row.thread_id,
                    "subject": row.subject,
                    "from": row.sender,
                    "snippet": row.body[:120].replace("\n", " "),
                }
            )
            if len(mentions) >= 5:
                return mentions
    return mentions


def _format_thread(emails: list[Email]) -> str:
    blocks = []
    for item in emails:
        blocks.append(
            "\n".join(
                [
                    f"[id={item.id}] From: {item.sender}",
                    f"To: {item.recipient}",
                    f"Date: {item.created_at.isoformat()}",
                    f"Subject: {item.subject}",
                    "",
                    item.body,
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def gather_urgency_facts(email: Email) -> dict:
    """
    收集紧急度相关的客观事实（不调用 LLM）。
    """
    now = datetime.now()
    hours_since_sent = round((now - email.created_at).total_seconds() / 3600, 1)

    thread_emails = (
        Email.query.filter_by(thread_id=email.thread_id)
        .order_by(Email.created_at.asc())
        .all()
    )

    is_inbound = email.recipient == PRIMARY_USER and email.sender != PRIMARY_USER
    is_outbound = email.sender == PRIMARY_USER

    user_reply_after = False
    user_reply_minutes = None
    for item in thread_emails:
        if item.created_at <= email.created_at:
            continue
        if item.sender == PRIMARY_USER:
            user_reply_after = True
            delta = item.created_at - email.created_at
            user_reply_minutes = round(delta.total_seconds() / 60)
            break

    sender_emails = (
        Email.query.filter(
            (Email.sender == email.sender) | (Email.recipient == email.sender)
        )
        .filter(Email.id != email.id)
        .order_by(Email.created_at.desc())
        .limit(8)
        .all()
    )
    sender_subjects = [e.subject for e in sender_emails]

    entity_tokens = _extract_entity_tokens(f"{email.subject}\n{email.body}")
    cross_thread = _cross_thread_mentions(email, entity_tokens)

    latest_in_thread = thread_emails[-1] if thread_emails else email
    is_latest_in_thread = latest_in_thread.id == email.id

    return {
        "email_id": email.id,
        "thread_id": email.thread_id,
        "subject": email.subject,
        "sender": email.sender,
        "sender_name": _display_name(email.sender),
        "recipient": email.recipient,
        "sent_at": email.created_at.isoformat(),
        "is_read": email.is_read,
        "is_inbound_to_user": is_inbound,
        "is_outbound_from_user": is_outbound,
        "hours_since_sent": hours_since_sent,
        "subject_flags": _subject_flags(email.subject),
        "user_replied_after": user_reply_after,
        "user_reply_minutes": user_reply_minutes,
        "is_latest_in_thread": is_latest_in_thread,
        "thread_message_count": len(thread_emails),
        "sender_recent_subjects": sender_subjects,
        "cross_thread_mentions": cross_thread,
        "entity_tokens": entity_tokens,
    }


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def classify_email_urgency(email_id: int) -> dict | None:
    """
    功能 6 入口：分析单封邮件的紧急程度。
    返回 None 表示邮件不存在。
    """
    email = Email.query.get(email_id)
    if email is None:
        return None

    facts = gather_urgency_facts(email)

    if facts["is_outbound_from_user"]:
        return {
            "email_id": email_id,
            "thread_id": email.thread_id,
            "subject": email.subject,
            "facts": facts,
            "score": None,
            "level": None,
            "action_needed": False,
            "reasoning": ["这是你发出的邮件，紧急程度分类仅适用于收到的邮件。"],
            "false_alarm_risk": None,
            "skipped": True,
        }

    thread_emails = (
        Email.query.filter_by(thread_id=email.thread_id)
        .order_by(Email.created_at.asc())
        .all()
    )

    raw = chat_completion(
        [
            {"role": "system", "content": CLASSIFY_PROMPT},
            {
                "role": "user",
                "content": (
                    f"当前日期：{datetime.now().date().isoformat()}\n\n"
                    f"目标邮件（id={email_id}）：\n"
                    f"From: {email.sender}\n"
                    f"Subject: {email.subject}\n"
                    f"Date: {email.created_at.isoformat()}\n\n"
                    f"{email.body}\n\n"
                    f"同线程对话：\n{_format_thread(thread_emails)}\n\n"
                    f"客观事实（facts）：\n"
                    f"{json.dumps(facts, ensure_ascii=False, indent=2)}"
                ),
            },
        ]
    )

    try:
        result = _parse_json_response(raw)
    except json.JSONDecodeError:
        result = {
            "score": 5,
            "level": "medium",
            "action_needed": facts["is_inbound_to_user"] and not facts["user_replied_after"],
            "reasoning": ["LLM 返回格式异常，已使用默认中等紧急度。"],
            "false_alarm_risk": "medium",
        }

    return {
        "email_id": email_id,
        "thread_id": email.thread_id,
        "subject": email.subject,
        "sender": email.sender,
        "sender_name": facts["sender_name"],
        "facts": facts,
        "score": result.get("score"),
        "level": result.get("level"),
        "action_needed": result.get("action_needed"),
        "reasoning": result.get("reasoning", []),
        "false_alarm_risk": result.get("false_alarm_risk"),
        "skipped": False,
    }
