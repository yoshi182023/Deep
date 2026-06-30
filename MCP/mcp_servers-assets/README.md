# Task API and MCP Server

## 🌐 Task API documentation

A FastAPI CRUD application for reminders.

- The tasks are stored in a list in memory.
- The application is using FastAPI and Pydantic for the API and data validation.
- The application is using uvicorn for the server.

Methods:

| Method | Endpoint           | Description         |
| ------ | ------------------ | ------------------- |
| GET    | `/tasks`           | Get all tasks       |
| POST   | `/tasks`           | Create a new task   |
| GET    | `/tasks/{task_id}` | Get a task by ID    |
| PUT    | `/tasks/{task_id}` | Update a task by ID |
| DELETE | `/tasks/{task_id}` | Delete a task by ID |

Run the API before using the MCP server:

- `uv sync`
- `uv run python api/app.py`

## ✅ MCP Server: setup instructions for Claude Desktop

**1. Make sure your MCP server file is accessible.**

Note the full path to the server file, `task_mcp_server.py`. For example:

- macOS/Linux: `/Users/YOUR_USERNAME/projects/task-app/task_mcp_server.py`
- Windows: `C:\Users\YOUR_USERNAME\projects\task-app\task_mcp_server.py`

**2. Locate your Claude Desktop config file:**

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**3. Edit the config file to add your MCP server.**

Open it in a text editor and add:

```json
{
  "mcpServers": {
    "task-manager": {
      "command": "/full/path/to/venv/bin/python",
      "args": ["/full/path/to/your/task_mcp_server.py"]
    }
  }
}
```

- Replace `/full/path/to/your/task_mcp_server.py` with the actual path from earlier.
- Make sure the command points to a virtual environment that can run your server.

**4. Restart Claude Desktop completely** (quit and reopen).

**5. Start your task API** on localhost:8000 before using the MCP tools:

```bash
# Start your API first
python api/app.py  # or however you run it
```

**6. Use the MCP server!**

In Claude Desktop, you should see a 🔌 icon indicating MCP servers are connected. Try asking:

- "Show me all my tasks"
- "Create a new task called 'Buy groceries'"
- "Mark task X as completed"

The MCP server will show up in the Claude Desktop interface, and Claude be able to use these tools to interact with your task API.

## Custom MCP Client using Ollama and LangChain

A LangChain-based MCP client that connects to the task manager server using a local Ollama model.

**Requirements:**

- Ollama installed with gemma4:e4b-it-q4_k_M model pulled
- Task API running on localhost:8000
- Built with `langchain-mcp-adapters`

**Setup:**

1. Install Ollama and pull the model:
```bash
ollama pull gemma4:e4b-it-q4_k_M
```

1. Update the server path in `mcp_client.py`:
   - Set `command` to your virtual environment's Python
   - Set `args` to the full path of `task_mcp_server.py`

2. Start the task API:
```bash
uv run python api/app.py
```

1. Run the client (it will automatically run the MCP server on startup):
```bash
uv run python mcp_client.py
```

**Usage:**

The client provides an interactive chat interface with conversation history. Type your requests and the agent will use MCP tools to interact with your tasks:

- "What tasks do I have?"
- "Add a task to review the quarterly report"
- "Delete task 3"

Type `quit`, `exit`, or `q` to end the session.

## DeepEval Test Suite for MCP Task Manager

The test suite validates:
1. Tool selection - Does the agent choose the right tool for the task?
2. Tool invocation - Are tools called with correct parameters?
3. Response quality - Are responses helpful, accurate, and contextual?
4. Conversation management - Is history maintained correctly?
5. Error handling - Does the system handle failures gracefully?

Usage:
```bash
uv run pytest test_mcp_system.py -v
```