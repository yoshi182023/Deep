from agents.client import chat_completion
from models import Email

SYSTEM_PROMPT = """You summarize email conversation threads in 2-3 concise sentences in Chinese.
Capture key participants, topics, and decisions. Omit irrelevant details."""


def format_thread(emails: list[Email]) -> str:
    blocks = []
    for email in emails:
        blocks.append(
            "\n".join(
                [
                    f"From: {email.sender}",
                    f"To: {email.recipient}",
                    f"Date: {email.created_at.isoformat()}",
                    f"Subject: {email.subject}",
                    "",
                    email.body,
                ]
            )
        )
    return "\n\n---\n\n".join(blocks)


def summarize_thread(thread_id: str) -> dict | None:
    emails = (
        Email.query.filter_by(thread_id=thread_id)
        .order_by(Email.created_at.asc())
        .all()
    )
    if not emails:
        return None

    summary = chat_completion(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Summarize this email thread (thread_id: {thread_id}):\n\n"
                    f"{format_thread(emails)}"
                ),
            },
        ]
    )

    return {
        "thread_id": thread_id,
        "message_count": len(emails),
        "summary": summary.strip(),
    }
