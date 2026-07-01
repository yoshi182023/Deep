# =============================================================================
# 第五步：承诺追踪（功能 5）
# -----------------------------------------------------------------------------
# 目标：扫描 pm@acme.com 发出的邮件，提取「我对别人做的承诺」。
#
# 设计思路：
#   1. gather_sent_emails() — 只取当前用户发出的邮件（不含收件箱里别人的 I'll）
#   2. extract_commitments() — LLM 从正文识别明确承诺（I'll / I will / 我会）
#   3. track_commitments()  — 入口：返回结构化 commitments + 中文 report
#
# 难点由 LLM 处理：区分「我会做」vs「我可以做」、解析 by Friday / tomorrow 等时间。
# =============================================================================
import json
import re
from datetime import datetime

from agents.client import chat_completion
from models import Email

PRIMARY_USER = "pm@acme.com"

EXTRACT_PROMPT = """你是邮件承诺提取助手。从产品经理（Alex / pm@acme.com）发出的邮件中，提取他对收件人做出的明确承诺。

只提取以下类型的承诺：
- I'll / I will / 我会 / 我将 等明确未来行动
- 带有截止时间的承诺（by Friday、tomorrow、周五前、明天）

不要提取：
- 问句（Can you...?、Can we...?）
- 可能性（I could、I might、maybe）
- 向对方索要时间（Can you give me until...）
- 纯信息陈述、感谢信

当前日期用于判断逾期：{today}

只输出 JSON，不要其他文字。格式：
{{
  "commitments": [
    {{
      "recipient": "收件人邮箱",
      "recipient_name": "收件人姓名",
      "quote": "承诺原文摘录",
      "thread_id": "线程 ID",
      "thread_subject": "线程主题",
      "sent_at": "邮件发送时间 ISO",
      "deadline_text": "截止时间原文或 null",
      "status": "overdue|due_soon|open",
      "status_reason": "状态说明（中文）"
    }}
  ]
}}
"""

REPORT_PROMPT = """请根据以下承诺列表，用中文生成「你的承诺」报告。
格式参考：

你的承诺：

1. 致 XXX（日期）：
   "承诺原文"
   线程：xxx
   状态：xxx

若无承诺，写「未发现明确承诺。」
不要编造列表中没有的内容。"""


def _display_name(email_address: str) -> str:
    local = email_address.split("@")[0]
    parts = local.replace(".", " ").replace("_", " ").split()
    return " ".join(p.capitalize() for p in parts)


def gather_sent_emails() -> list[Email]:
    """拉取当前用户发出的全部邮件，按时间升序"""
    return (
        Email.query.filter_by(sender=PRIMARY_USER)
        .order_by(Email.created_at.asc())
        .all()
    )


def format_sent_emails(emails: list[Email]) -> str:
    """将已发送邮件格式化为 LLM 输入文本"""
    blocks = []
    for email in emails:
        blocks.append(
            "\n".join(
                [
                    f"To: {email.recipient}",
                    f"To name: {_display_name(email.recipient)}",
                    f"Date: {email.created_at.isoformat()}",
                    f"Subject: {email.subject}",
                    f"Thread: {email.thread_id}",
                    "",
                    email.body,
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def _parse_json_response(text: str) -> dict:
    """从 LLM 回复中解析 JSON（兼容 ```json 代码块）"""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    return json.loads(text)


def extract_commitments(emails: list[Email]) -> list[dict]:
    """调用 LLM 从已发送邮件中提取承诺列表"""
    if not emails:
        return []

    today = datetime.now().date().isoformat()
    raw = chat_completion(
        [
            {
                "role": "system",
                "content": EXTRACT_PROMPT.format(today=today),
            },
            {
                "role": "user",
                "content": (
                    f"以下是 {len(emails)} 封已发送邮件，请提取承诺：\n\n"
                    f"{format_sent_emails(emails)}"
                ),
            },
        ]
    )

    try:
        data = _parse_json_response(raw)
        return data.get("commitments", [])
    except json.JSONDecodeError:
        return []


def build_report(commitments: list[dict]) -> str:
    """根据承诺列表生成中文可读报告"""
    if not commitments:
        return "你的承诺：\n\n未发现明确承诺。"

    report = chat_completion(
        [
            {"role": "system", "content": REPORT_PROMPT},
            {
                "role": "user",
                "content": json.dumps(commitments, ensure_ascii=False, indent=2),
            },
        ]
    )
    return report.strip()


def track_commitments() -> dict:
    """
    功能 5 入口：扫描已发送邮件，返回承诺列表与报告。
    """
    emails = gather_sent_emails()
    commitments = extract_commitments(emails)
    report = build_report(commitments)

    return {
        "sent_email_count": len(emails),
        "commitment_count": len(commitments),
        "commitments": commitments,
        "report": report,
    }
