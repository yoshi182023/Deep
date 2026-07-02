# 未读邮件摘要：功能 2 — 按发件人分组汇总未读收件
from collections import defaultdict

from agents.client import chat_completion
from models import Email

# 当前登录用户，只摘要发给他且未读的邮件
PRIMARY_USER = "pm@acme.com"

# 发给 LLM 的系统提示：要求中文输出、按发件人分组、bullet 格式
SYSTEM_PROMPT = """用中文生成未读邮件摘要。
按发件人分组，每组下列出简洁要点（每条一行，以 - 开头）。
必须涵盖输入中的每一封未读邮件，突出紧急的事项。
使用如下格式：

未读摘要（N 封邮件）：

来自 发件人（M 封）：
- 要点
"""


def format_unread(emails: list[Email]) -> str:
    """将未读邮件按发件人分组，拼成 LLM 可读的文本"""
    by_sender: dict[str, list[Email]] = defaultdict(list)
    for email in emails:
        by_sender[email.sender].append(email)

    sections = []
    for sender, sender_emails in sorted(by_sender.items()):
        blocks = []
        for email in sender_emails:
            blocks.append(
                "\n".join(
                    [
                        f"Subject: {email.subject}",
                        f"Date: {email.created_at.isoformat()}",
                        f"Thread: {email.thread_id}",
                        email.body,
                    ]
                )
            )
        sections.append(f"From: {sender} ({len(sender_emails)} emails)\n\n" + "\n\n---\n\n".join(blocks))

    return "\n\n====\n\n".join(sections)


def digest_unread() -> dict:
    """拉取未读邮件并生成摘要，返回 unread_count + digest 文本"""
    # 查询：未读 + 收件人是当前用户
    emails = (
        Email.query.filter_by(is_read=False, recipient=PRIMARY_USER)
        .order_by(Email.created_at.desc())
        .all()
    )

    # 无未读时直接返回，不调用 LLM
    if not emails:
        return {
            "unread_count": 0,
            "digest": "没有未读邮件。",
        }

    # 调用 OpenAI 生成按发件人分组的摘要
    digest = chat_completion(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"以下是 {len(emails)} 封未读邮件，请生成摘要：\n\n"
                    f"{format_unread(emails)}"
                ),
            },
        ]
    )

    return {
        "unread_count": len(emails),
        "digest": digest.strip(),
    }
