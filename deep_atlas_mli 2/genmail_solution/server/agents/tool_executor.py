import uuid
import requests
from typing import Any

API_BASE = "http://localhost:5001"


def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a tool by calling the appropriate API endpoint.
    Returns a standardized result dict with 'success', 'data', and optional 'error' keys.
    """
    try:
        if tool_name == "list_emails":
            params = {}
            if "thread_id" in tool_input:
                params["thread_id"] = tool_input["thread_id"]
            if "is_read" in tool_input:
                params["is_read"] = str(tool_input["is_read"]).lower()
            if "sender" in tool_input:
                params["sender"] = tool_input["sender"]
            if "recipient" in tool_input:
                params["recipient"] = tool_input["recipient"]

            response = requests.get(f"{API_BASE}/emails", params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        elif tool_name == "get_email":
            email_id = tool_input["email_id"]
            response = requests.get(f"{API_BASE}/emails/{email_id}")
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        elif tool_name == "search_emails_by_content":
            params = {"q": tool_input["query"]}
            if "is_read" in tool_input:
                params["is_read"] = str(tool_input["is_read"]).lower()
            if "sender" in tool_input:
                params["sender"] = tool_input["sender"]
            if "recipient" in tool_input:
                params["recipient"] = tool_input["recipient"]
            if "thread_id" in tool_input:
                params["thread_id"] = tool_input["thread_id"]
            if "limit" in tool_input:
                params["limit"] = tool_input["limit"]

            response = requests.get(f"{API_BASE}/emails/search", params=params)
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        elif tool_name == "create_email":
            payload = {
                "sender": tool_input["sender"],
                "recipient": tool_input["recipient"],
                "subject": tool_input["subject"],
                "body": tool_input["body"]
            }
            if "thread_id" in tool_input:
                payload["thread_id"] = tool_input["thread_id"]

            response = requests.post(f"{API_BASE}/emails", json=payload)
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        elif tool_name == "mark_email_read":
            email_id = tool_input["email_id"]
            response = requests.patch(f"{API_BASE}/emails/{email_id}/read")
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        elif tool_name == "mark_email_unread":
            email_id = tool_input["email_id"]
            response = requests.put(
                f"{API_BASE}/emails/{email_id}",
                json={"is_read": False}
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        elif tool_name == "delete_email":
            email_id = tool_input["email_id"]
            response = requests.delete(f"{API_BASE}/emails/{email_id}")
            response.raise_for_status()
            return {"success": True, "data": None}

        elif tool_name == "get_threads":
            response = requests.get(f"{API_BASE}/threads")
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        elif tool_name == "get_stats":
            response = requests.get(f"{API_BASE}/stats")
            response.raise_for_status()
            return {"success": True, "data": response.json()}

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

    except requests.exceptions.HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Execution error: {str(e)}"
        }
