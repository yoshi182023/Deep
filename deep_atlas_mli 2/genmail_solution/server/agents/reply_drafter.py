from typing import List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from agents.logger import TrackedLLM

MAX_RETRIES = 3


class ReplyState(TypedDict):
    email_id: int
    thread_emails: List[dict]
    thread_context: str
    draft: str
    feedback: Optional[str]
    tone: Optional[str]
    previous_draft: Optional[str]
    thread_id: str
    recipient: str
    subject: str
    error: Optional[str]
    retry_count: int


def fetch_thread_context(state: ReplyState) -> ReplyState:
    from models import Email

    email = Email.query.get(state["email_id"])
    if not email:
        return {**state, "thread_context": "", "thread_emails": [], "error": f"Email {state['email_id']} not found"}

    thread_emails = Email.query.filter_by(
        thread_id=email.thread_id
    ).order_by(Email.created_at.asc()).all()

    thread_context = "\n\n".join([
        f"From: {e.sender}\n"
        f"To: {e.recipient}\n"
        f"Date: {e.created_at}\n"
        f"Subject: {e.subject}\n"
        f"Body:\n{e.body}"
        for e in thread_emails
    ])

    latest_sender = thread_emails[-1].sender
    recipient = latest_sender if latest_sender != "pm@acme.com" else email.sender
    subject = email.subject if not email.subject.startswith("Re:") else email.subject
    subject = f"Re: {subject}" if not subject.startswith("Re:") else subject

    return {
        **state,
        "thread_context": thread_context,
        "thread_emails": [e.to_dict() for e in thread_emails],
        "thread_id": email.thread_id,
        "recipient": recipient,
        "subject": subject,
        "error": None
    }


def context_found(state: ReplyState) -> str:
    return "end" if state.get("error") else "draft"


def draft_reply(state: ReplyState) -> ReplyState:
    base_llm = ChatOllama(model="llama3.2", temperature=0.7)
    operation = "refine" if state.get("previous_draft") else "draft"
    llm = TrackedLLM(base_llm, agent_name="reply_drafter", operation=operation)

    if state.get("previous_draft"):
        tone_instruction = ""
        if state.get("tone") == "formal":
            tone_instruction = "\n\nApply FORMAL tone: Use formal business language, avoid contractions, use professional salutations and closings."
        elif state.get("tone") == "concise":
            tone_instruction = "\n\nApply CONCISE tone: Reduce to essential points only, max 3 sentences per paragraph, eliminate unnecessary words."
        elif state.get("tone") == "friendly":
            tone_instruction = "\n\nApply FRIENDLY tone: Use warm conversational language, show personality, use casual but professional phrasing."

        feedback_instruction = f"\n\nUser feedback: {state['feedback']}" if state.get("feedback") else ""

        prompt = f"""You are refining an email draft for Alex at pm@acme.com.

Original draft:
{state['previous_draft']}
{tone_instruction}{feedback_instruction}

Rewrite the draft incorporating the tone adjustment and/or feedback. Sign as "Alex".

IMPORTANT: Return ONLY the refined email body text. Do not include any explanations, headers, or extra text."""
    else:
        prompt = f"""You are drafting an email reply for Alex at pm@acme.com.

Thread context (chronological order):
{state['thread_context']}

Analyze the thread and draft a professional reply that:
- Addresses the key points and questions raised
- Maintains a helpful, collaborative tone
- Is clear and actionable
- Signs as "Alex"

Return ONLY the email body text, no subject line or headers."""

    try:
        response = llm.invoke(prompt)
        return {**state, "draft": response.content.strip(), "error": None}
    except Exception as e:
        return {**state, "draft": "", "error": str(e), "retry_count": state["retry_count"] + 1}


def should_retry(state: ReplyState) -> str:
    if state.get("error") and state["retry_count"] < MAX_RETRIES:
        return "retry"
    return "end"


def create_workflow():
    workflow = StateGraph(ReplyState)

    workflow.add_node("fetch_thread_context", fetch_thread_context)
    workflow.add_node("draft_reply", draft_reply)

    workflow.set_entry_point("fetch_thread_context")
    workflow.add_conditional_edges("fetch_thread_context", context_found, {"draft": "draft_reply", "end": END})
    workflow.add_conditional_edges("draft_reply", should_retry, {"retry": "draft_reply", "end": END})

    return workflow.compile()


def draft_reply_for_email(email_id, feedback=None, tone=None, previous_draft=None):
    app = create_workflow()
    result = app.invoke({
        "email_id": email_id,
        "thread_emails": [],
        "thread_context": "",
        "draft": "",
        "feedback": feedback,
        "tone": tone,
        "previous_draft": previous_draft,
        "thread_id": "",
        "recipient": "",
        "subject": "",
        "error": None,
        "retry_count": 0
    })

    return {
        "draft": result["draft"],
        "thread_id": result["thread_id"],
        "recipient": result["recipient"],
        "subject": result["subject"]
    }
