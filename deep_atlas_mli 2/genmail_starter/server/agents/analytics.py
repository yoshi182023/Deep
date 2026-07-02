# =============================================================================
# 第四步：统计仪表盘（功能 4）
# -----------------------------------------------------------------------------
# 目标：超越 GET /stats 的基础计数，生成「收件箱智能分析」报告。
#
# 设计思路（两步走，比纯 LLM 更稳）：
#   1. gather_inbox_facts() — 用 SQL 从数据库算出客观事实（邮件量、最忙日、
#      往来最多的人、最长/最近线程、等待回复线索等）
#   2. inbox_analytics()   — 把事实交给 LLM，写成 README 示例格式的中文报告
#

# =============================================================================
import json
from datetime import datetime

from agents.client import chat_completion
from models import Email, db

# 当前用户（产品经理收件箱的主人）
PRIMARY_USER = "pm@acme.com"

# LLM 系统提示：根据 Python 算好的事实写报告，禁止编造
SYSTEM_PROMPT = """根据提供的收件箱统计数据，用中文生成「收件箱智能分析」报告。
包含三个板块：邮件量、人员、线程。
在人员板块指出往来最多的人、可能等待回复的人。
不要编造数据中不存在的信息。
使用简洁的 bullet 列表，风格参考以下示例：

收件箱智能分析：

邮件量：
- 共 N 封邮件（M 封未读）
- ...

人员：
- 往来最多：...
- 等待回复：...

线程：
- 最长：...
- 最近：...
"""


def _display_name(email_address: str) -> str:
    """把邮箱转成 README 风格的人名（david.park@acme.com → David Park）"""
    local = email_address.split("@")[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    return " ".join(p.capitalize() for p in parts)


def gather_inbox_facts() -> dict:
    """
    从数据库收集收件箱统计事实（不调用 LLM）。
    返回 dict，后续会 json.dumps 后喂给 LLM。
    """
    total_emails = Email.query.count()
    unread_count = Email.query.filter_by(is_read=False).count()
    thread_count = db.session.query(Email.thread_id).distinct().count()

    # 最忙的一天：按日期分组计数，取邮件最多的一天
    busiest_row = (
        db.session.query(
            db.func.date(Email.created_at).label("day"),
            db.func.count(Email.id).label("count"),
        )
        .group_by(db.func.date(Email.created_at))
        .order_by(db.desc("count"))
        .first()
    )
    busiest_day = {
        "date": str(busiest_row.day) if busiest_row else None,
        "count": busiest_row.count if busiest_row else 0,
    }

    # 往来最多：统计每个外部联系人与 pm 的邮件往来次数（发件或收件都算）
    contact_counts: dict[str, int] = {}
    for email in Email.query.all():
        for party in (email.sender, email.recipient):
            if party != PRIMARY_USER:
                contact_counts[party] = contact_counts.get(party, 0) + 1

    most_frequent = None
    if contact_counts:
        top_email, top_count = max(contact_counts.items(), key=lambda item: item[1])
        most_frequent = {
            "email": top_email,
            "name": _display_name(top_email),
            "count": top_count,
        }

    # 按线程聚合：用于找最长线程、最近活跃线程
    thread_rows = (
        db.session.query(
            Email.thread_id,
            db.func.min(Email.subject).label("subject"),
            db.func.count(Email.id).label("message_count"),
            db.func.min(Email.created_at).label("first_at"),
            db.func.max(Email.created_at).label("last_at"),
        )
        .group_by(Email.thread_id)
        .all()
    )

    longest_thread = None
    most_recent_thread = None
    if thread_rows:
        longest = max(thread_rows, key=lambda t: t.message_count)
        span_days = (longest.last_at - longest.first_at).days
        longest_thread = {
            "thread_id": longest.thread_id,
            "subject": longest.subject,
            "message_count": longest.message_count,
            "span_days": span_days,
        }

        recent = max(thread_rows, key=lambda t: t.last_at)
        most_recent_thread = {
            "thread_id": recent.thread_id,
            "subject": recent.subject,
            "last_message_at": recent.last_at.isoformat(),
        }

    # 等待回复：线程内最后一封若是别人发给 pm，说明对方在等回复
    awaiting_reply: list[dict] = []
    for row in thread_rows:
        last_email = (
            Email.query.filter_by(thread_id=row.thread_id)
            .order_by(Email.created_at.desc())
            .first()
        )
        if (
            last_email
            and last_email.recipient == PRIMARY_USER
            and last_email.sender != PRIMARY_USER
        ):
            awaiting_reply.append(
                {
                    "sender": last_email.sender,
                    "name": _display_name(last_email.sender),
                    "subject": last_email.subject,
                    "thread_id": row.thread_id,
                    "last_message_at": last_email.created_at.isoformat(),
                }
            )

    return {
        "total_emails": total_emails,
        "unread_count": unread_count,
        "thread_count": thread_count,
        "busiest_day": busiest_day,
        "most_frequent_contact": most_frequent,
        "longest_thread": longest_thread,
        "most_recent_thread": most_recent_thread,
        "awaiting_reply": awaiting_reply,
        "generated_at": datetime.now().isoformat(),
    }


def format_facts_for_llm(facts: dict) -> str:
    """把事实 dict 格式化成 LLM 易读的 JSON 文本"""
    return json.dumps(facts, ensure_ascii=False, indent=2)


def inbox_analytics() -> dict:
    """
    功能 4 入口：先 gather 事实，再调 LLM 生成 report。
    返回结构化 JSON（含原始 facts + 中文 report），供 API 和前端使用。
    """
    facts = gather_inbox_facts()

    report = chat_completion(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "请根据以下收件箱统计数据生成分析报告 每个点一句话：\n\n"
                    f"{format_facts_for_llm(facts)}"
                ),
            },
        ]
    )

    return {
        "total_emails": facts["total_emails"],
        "unread_count": facts["unread_count"],
        "thread_count": facts["thread_count"],
        "facts": facts,
        "report": report.strip(),
    }
