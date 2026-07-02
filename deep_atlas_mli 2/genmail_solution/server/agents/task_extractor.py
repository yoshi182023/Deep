import json
from typing import List, TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from pydantic import BaseModel
from agents.logger import TrackedLLM

MAX_RETRIES = 3


class ActionItem(BaseModel):
    description: str
    priority: str
    email_id: int
    thread_id: str


class AgentState(TypedDict):
    emails: List[dict]
    emails_text: str
    raw_response: str
    tasks: List[ActionItem]
    error: Optional[str]
    retry_count: int


def format_emails(state: AgentState) -> AgentState:
    emails_text = "\n\n".join([
        f"Email ID: {e['id']}\n"
        f"Thread ID: {e['thread_id']}\n"
        f"From: {e['sender']}\n"
        f"Subject: {e['subject']}\n"
        f"Date: {e['created_at']}\n"
        f"Body: {e['body']}"
        for e in state["emails"]
    ])
    return {**state, "emails_text": emails_text}


def extract_tasks(state: AgentState) -> AgentState:
    base_llm = ChatOllama(model="llama3.2", temperature=0)
    llm = TrackedLLM(base_llm, agent_name="task_extractor", operation="extract")

    prompt = f"""You are an AI assistant helping an employee at acme.com prioritize their inbox.

Analyze these unread emails and extract concrete action items:

{state['emails_text']}

Extract action items that are:
- Explicit requests for decisions or input
- Commitments you need to fulfill
- Questions that need responses
- Upcoming meetings or deadlines

For each action item:
- Write a clear, actionable description (start with verb: "Respond to...", "Review...", "Decide on...")
- Set priority based on urgency and importance (high/medium/low)
- Link to the source email_id and thread_id

Skip:
- Pure FYI emails
- Already completed items
- Vague or unclear requests

Return your response as a JSON array of objects with this structure:
[
  {{"description": "Respond to...", "priority": "high", "email_id": 123, "thread_id": "abc"}},
  {{"description": "Review...", "priority": "medium", "email_id": 124, "thread_id": "xyz"}}
]

IMPORTANT: Return ONLY the JSON array, no additional text."""

    try:
        response = llm.invoke(prompt)
        return {**state, "raw_response": response.content, "error": None}
    except Exception as e:
        return {**state, "raw_response": "", "error": str(e)}


def parse_response(state: AgentState) -> AgentState:
    if state.get("error"):
        return {**state, "tasks": [], "retry_count": state["retry_count"] + 1}

    try:
        raw_text = state["raw_response"].strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        tasks_data = json.loads(raw_text)
        tasks = [ActionItem(**task) for task in tasks_data]
        return {**state, "tasks": tasks, "error": None}
    except Exception as e:
        return {**state, "tasks": [], "error": str(e), "retry_count": state["retry_count"] + 1}


def should_retry(state: AgentState) -> str:
    if state.get("error") and state["retry_count"] < MAX_RETRIES:
        return "retry"
    return "end"


def validate_tasks(state: AgentState) -> AgentState:
    valid_email_ids = {e["id"] for e in state["emails"]}
    valid_thread_ids = {e["thread_id"] for e in state["emails"]}
    verified_tasks = [
        t for t in state["tasks"]
        if t.email_id in valid_email_ids and t.thread_id in valid_thread_ids
    ]
    return {**state, "tasks": verified_tasks}


def create_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("format_emails", format_emails)
    workflow.add_node("extract_tasks", extract_tasks)
    workflow.add_node("parse_response", parse_response)
    workflow.add_node("validate_tasks", validate_tasks)

    workflow.set_entry_point("format_emails")
    workflow.add_edge("format_emails", "extract_tasks")
    workflow.add_edge("extract_tasks", "parse_response")
    workflow.add_conditional_edges("parse_response", should_retry, {"retry": "extract_tasks", "end": "validate_tasks"})
    workflow.add_edge("validate_tasks", END)

    return workflow.compile()


def extract_tasks_from_emails(emails):
    if not emails:
        return []

    app = create_workflow()
    result = app.invoke({"emails": emails, "emails_text": "", "raw_response": "", "tasks": [], "error": None, "retry_count": 0})

    return result["tasks"]
