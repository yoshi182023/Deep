import json
import re
from typing import Any
from langchain_ollama import ChatOllama
from agents.logger import TrackedLLM

EMAIL_TOOLS = [
    {"name": "list_emails",                "params": "thread_id?, is_read?, sender?, recipient?"},
    {"name": "get_email",                  "params": "email_id"},
    {"name": "search_emails_by_content",   "params": "query, is_read?, sender?, recipient?, thread_id?, limit?"},
    {"name": "create_email",               "params": "sender, recipient, subject, body, thread_id?"},
    {"name": "mark_email_read",            "params": "email_id"},
    {"name": "mark_email_unread",          "params": "email_id"},
    {"name": "delete_email",               "params": "email_id"},
    {"name": "get_threads",                "params": ""},
    {"name": "get_stats",                  "params": ""},
]

TOOL_DESCRIPTIONS = "\n".join(
    f"- {t['name']}({t['params']})" for t in EMAIL_TOOLS
)

# Each item in the output array must be {"name": "<tool>", "input": {<params>}}
SELECTION_PROMPT = (
    "Select tools for an email client.\n"
    "Output ONLY a valid JSON array. Each element must be an object with keys 'name' and 'input'.\n\n"
    f"Tools:\n{TOOL_DESCRIPTIONS}\n\n"
    "Examples:\n"
    'Input: "show unread"\n'
    'Output: [{"name":"list_emails","input":{"is_read":false}}]\n\n'
    'Input: "search Phoenix"\n'
    'Output: [{"name":"search_emails_by_content","input":{"query":"Phoenix"}}]\n\n'
    'Input: "inbox stats"\n'
    'Output: [{"name":"get_stats","input":{}}]\n\n'
    'Input: "all threads"\n'
    'Output: [{"name":"get_threads","input":{}}]\n\n'
)


def extract_json_array(text: str) -> list:
    text = re.sub(r"```(?:json)?\n?", "", text).strip()

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            # Standard format: [{"name": ..., "input": ...}]
            if parsed and isinstance(parsed[0], dict) and "name" in parsed[0]:
                return parsed
            # Flat format: ["tool_name", {params}]
            if parsed and isinstance(parsed[0], str):
                params = parsed[1] if len(parsed) > 1 and isinstance(parsed[1], dict) else {}
                return [{"name": parsed[0], "input": params}]
        except json.JSONDecodeError:
            pass

    # Fallback for ["name":"x","input":{...}] — invalid JSON, extract with regex
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', text)
    if name_match:
        input_match = re.search(r'"input"\s*:\s*(\{.*?\})', text, re.DOTALL)
        tool_input = {}
        if input_match:
            try:
                tool_input = json.loads(input_match.group(1))
            except json.JSONDecodeError:
                pass
        return [{"name": name_match.group(1), "input": tool_input}]

    return []


class ToolSelectionAgent:

    def __init__(self, model: str = "llama3.2"):
        base_llm = ChatOllama(model=model, temperature=0)
        self.llm = TrackedLLM(base_llm, agent_name="tool_selector", operation="select")

    def select_tools(self, user_input: str) -> list[dict[str, Any]]:
        prompt = SELECTION_PROMPT + f'Input: "{user_input}"\nOutput:'
        try:
            response = self.llm.invoke(prompt)
            tools = extract_json_array(response.content)
            valid_names = {t["name"] for t in EMAIL_TOOLS}
            return [t for t in tools if isinstance(t, dict) and t.get("name") in valid_names]
        except Exception:
            return []
