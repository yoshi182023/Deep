# 发件人主题分析：功能 3 — 分析某发件人的全部邮件并识别主题聚类
from agents.client import chat_completion
from models import Email

# 发给 LLM 的系统提示：中文输出、主题聚类、带示例
SYSTEM_PROMPT = """请用中文分析指定发件人的邮件，识别主题聚类。
将邮件按主题分组，主题要具体明确，每组给出代表性示例（bullet 列表）。
注明每组大致涉及的邮件数量。
使用如下格式：

发件人：xxx@acme.com（N 封邮件）

主题：
1. 主题名称（M 封）
   - 示例要点
   - 示例要点
"""


def format_sender_emails(emails: list[Email]) -> str:
    """将该发件人的所有邮件拼成 LLM 可读文本"""
    blocks = []
    for email in emails:
        blocks.append(
            "\n".join(
                [
                    f"To: {email.recipient}",
                    f"Date: {email.created_at.isoformat()}",
                    f"Subject: {email.subject}",
                    f"Thread: {email.thread_id}",
                    "",
                    email.body,
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def analyze_sender_topics(sender: str) -> dict | None:
    """分析某发件人的全部邮件，返回主题聚类报告"""
    emails = (
        Email.query.filter_by(sender=sender)
        .order_by(Email.created_at.asc())
        .all()
    )
    if not emails:
        return None

    analysis = chat_completion(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"以下是发件人 {sender} 的 {len(emails)} 封邮件，请做主题聚类分析：\n\n"
                    f"{format_sender_emails(emails)}"
                ),
            },
        ]
    )

    return {
        "sender": sender,
        "email_count": len(emails),
        "analysis": analysis.strip(),
    }
