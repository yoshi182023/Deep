import requests
from mcp.server.fastmcp import FastMCP
from typing import Optional


mcp = FastMCP("Task Manager")
API_BASE_URL = "http://localhost:8000"


@mcp.tool()
def get_tasks() -> list[dict] | str:
    """Get all tasks from the task manager. Returns a list of all tasks with
    their IDs, titles, descriptions, and completion status."""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Return a string so the LLM can read and relay the error message.
        return f"Error fetching tasks: {e.response.status_code} {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching tasks: {str(e)}"


@mcp.tool()
def create_task(
    title: str,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> dict | str:
    try:
        response = requests.post(
            f"{API_BASE_URL}/tasks",
            json={
                "title": title,
                "description": description or "",
                "completed": completed or False,
            },
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return f"Error creating task: {e.response.status_code} {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error creating task: {str(e)}"


@mcp.tool()
def get_task(task_id: str) -> dict | str:
    """Get a specific task by its ID. Returns the task details including title,
    description, and completion status."""
    try:
        response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Error: task with ID '{task_id}' was not found."
        return f"Error fetching task: {e.response.status_code} {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error fetching task: {str(e)}"


@mcp.tool()
def update_task(
    task_id: str,
    title: str = None,
    description: str = None,
    completed: bool = None,
) -> dict | str:
    """Update an existing task. Provide the task ID and any fields you want to
    update (title, description, and/or completed status)."""
    try:
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if completed is not None:
            update_data["completed"] = completed

        response = requests.put(f"{API_BASE_URL}/tasks/{task_id}", json=update_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Error: task with ID '{task_id}' was not found."
        return f"Error updating task: {e.response.status_code} {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error updating task: {str(e)}"


@mcp.tool()
def delete_task(task_id: str) -> dict | str:
    """Delete a task by its ID. Permanently removes the task from the task manager."""
    try:
        response = requests.delete(f"{API_BASE_URL}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Error: task with ID '{task_id}' was not found."
        return f"Error deleting task: {e.response.status_code} {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error deleting task: {str(e)}"


if __name__ == "__main__":
    mcp.run()
