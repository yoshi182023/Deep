import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Task Manager")
API_BASE_URL = "http://localhost:8000"


# FILL_THIS_IN: Add the decorator that exposes this function as an MCP tool
def get_tasks() -> list[dict]:
    """Get all tasks from the task manager. Returns a list of all tasks with their IDs, titles, descriptions, and completion status."""
    try:
        # FILL_THIS_IN: Make a GET request to fetch all tasks from the API
        # Then return the JSON response
        pass
    except requests.exceptions.RequestException as e:
        # Raise exception instead of returning error dict to match return type
        raise Exception(f"Failed to fetch tasks: {str(e)}")


@mcp.tool()
def create_task(title: str, description: str = "", completed: bool = False) -> dict:
    """Create a new task in the task manager. Requires a title, and optionally accepts a description and completed status."""
    try:
        # FILL_THIS_IN: Make a POST request to create a new task with the provided parameters
        pass
    except requests.exceptions.RequestException as e:
        # Raise exception instead of returning error dict
        raise Exception(f"Failed to create task: {str(e)}")


@mcp.tool()
def get_task(task_id: str) -> dict:
    """Get a specific task by its ID. Returns the task details including title, description, and completion status."""
    try:
        # FILL_THIS_IN: Make a GET request to fetch a specific task by its ID
        # The task_id should be part of the URL path
        pass
    except requests.exceptions.RequestException as e:
        # Raise exception instead of returning error dict
        raise Exception(f"Failed to fetch task: {str(e)}")


@mcp.tool()
def update_task(
    task_id: str, title: str = None, description: str = None, completed: bool = None
) -> dict:
    """Update an existing task. Provide the task ID and any fields you want to update (title, description, and/or completed status)."""
    try:
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if completed is not None:
            update_data["completed"] = completed

        # FILL_THIS_IN: Make a PUT request to update the task with the update_data
        pass
    except requests.exceptions.RequestException as e:
        # Raise exception instead of returning error dict
        raise Exception(f"Failed to update task: {str(e)}")


@mcp.tool()
def delete_task(task_id: str) -> dict:
    """Delete a task by its ID. Permanently removes the task from the task manager."""
    try:
        # FILL_THIS_IN: Make a DELETE request to remove the task
        pass
    except requests.exceptions.RequestException as e:
        # Raise exception instead of returning error dict
        raise Exception(f"Failed to delete task: {str(e)}")


if __name__ == "__main__":
    mcp.run()
