# HTTP 请求库，用于调用底层 Task API
import requests
# FastMCP：快速创建 MCP 服务器的框架
from mcp.server.fastmcp import FastMCP

# 创建 MCP 服务器实例，名称为 "Task Manager"
mcp = FastMCP("Task Manager")
# 底层 REST API 的基础地址
API_BASE_URL = "http://localhost:8000"


# FILL_THIS_IN: 添加装饰器，将此函数暴露为 MCP 工具
# 提示：参考下方 create_task 的 @mcp.tool() 写法
def get_tasks() -> list[dict]:
    """Get all tasks from the task manager. Returns a list of all tasks with their IDs, titles, descriptions, and completion status."""
    try:
        # FILL_THIS_IN: 发送 GET 请求获取所有任务
        # 然后 return response.json() 返回 JSON 响应
        pass
    except requests.exceptions.RequestException as e:
        # 网络请求失败时抛出异常（而非返回错误字典），以匹配返回类型
        raise Exception(f"Failed to fetch tasks: {str(e)}")


# @mcp.tool() 装饰器：将函数注册为 LLM 可调用的 MCP 工具
@mcp.tool()
def create_task(title: str, description: str = "", completed: bool = False) -> dict:
    """Create a new task in the task manager. Requires a title, and optionally accepts a description and completed status."""
    try:
        # FILL_THIS_IN: 发送 POST 请求创建新任务
        # 请求体 JSON 需包含 title、description、completed 三个字段
        pass
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to create task: {str(e)}")


@mcp.tool()
def get_task(task_id: str) -> dict:
    """Get a specific task by its ID. Returns the task details including title, description, and completion status."""
    try:
        # FILL_THIS_IN: 发送 GET 请求获取指定任务
        # task_id 应放在 URL 路径中，例如 f"{API_BASE_URL}/tasks/{task_id}"
        pass
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch task: {str(e)}")


@mcp.tool()
def update_task(
    task_id: str, title: str = None, description: str = None, completed: bool = None
) -> dict:
    """Update an existing task. Provide the task ID and any fields you want to update (title, description, and/or completed status)."""
    try:
        # 只收集用户实际传入的字段，支持部分更新
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if description is not None:
            update_data["description"] = description
        if completed is not None:
            update_data["completed"] = completed

        # FILL_THIS_IN: 发送 PUT 请求更新任务，请求体为 update_data
        pass
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to update task: {str(e)}")


@mcp.tool()
def delete_task(task_id: str) -> dict:
    """Delete a task by its ID. Permanently removes the task from the task manager."""
    try:
        # FILL_THIS_IN: 发送 DELETE 请求删除指定 task_id 的任务
        pass
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to delete task: {str(e)}")


# 直接运行此文件时，启动 MCP 服务器（通过 stdio 等待客户端连接）
if __name__ == "__main__":
    mcp.run()
