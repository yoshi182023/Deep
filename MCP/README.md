MCP Task Manager - Build Your First MCP Application
MCP 任务管理器 - 构建你的第一个 MCP 应用


使用模型上下文协议（Model Context Protocol）将 LLM 连接到外部工具
⚠️ 本练习引入了一些新的依赖项。请研究附带的 pyproject.toml 文件，然后选择以下方式之一：
将其与现有的 deep_atlas 环境合并，将新依赖项安装到你原来的环境中。
使用 uv sync 为本练习单独创建一个新的虚拟环境。
了解 MCP 服务器如何向 LLM 客户端暴露工具
构建一个封装 REST API 的 MCP 服务器
配置 MCP 客户端以发现并使用服务器工具
在无状态 Agent 架构中管理对话状态
本练习将引导你构建一个完整的 MCP 应用，其中三个组件协同工作：
任务 API（FastAPI）：用于管理任务的 REST API——已完成
MCP 服务器（FastMCP）：封装 API 并将其暴露为 MCP 工具——由你完成
MCP 客户端（LangChain）：连接到服务器并实现对话式任务管理——由你完成

最终效果？一个聊天界面，你可以用自然语言创建、读取、更新和删除任务，LLM 在底层调用你的 MCP 工具
前置条件
已安装 Ollama 并运行 llama3.2 模型

对以下内容有基本了解：
Python async/await 语法
HTTP 方法（GET、POST、PUT、DELETE）

JSON 请求/响应格式
1. 设置你的环境

```bash
# Create and activate a virtual environment
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
# 安装依赖项
pip install fastapi uvicorn requests mcp langchain-mcp-adapters langchain langchain-ollama
```
2. 启动任务 API
FastAPI 服务器已完整提供作为参考。请先启动它：

```bash
uv run python api/app.py
```

The API will run on http://localhost:8000. Keep this running in a separate terminal.
API 将在 http://localhost:8000 上运行。请在单独的终端中保持其运行。

3. 查看 API 文档
在实现 MCP 服务器之前，先了解有哪些可用的端点：
GET /tasks - 列出所有任务

POST /tasks - Create a new task
POST /tasks - 创建新任务

GET /tasks/{task_id} - Get a specific task
GET /tasks/{task_id} - 获取特定任务

PUT /tasks/{task_id} - Update a task
PUT /tasks/{task_id} - 更新任务

DELETE /tasks/{task_id} - Delete a task
DELETE /tasks/{task_id} - 删除任务

You can test these endpoints at http://localhost:8000/docs (FastAPI's interactive documentation).
你可以在 http://localhost:8000/docs（FastAPI 交互式文档）测试这些端点。

Part 1: Build the MCP Server
第一部分：构建 MCP 服务器

Goal: Create an MCP server that exposes the Task API as tools that an LLM can use.
目标：创建一个 MCP 服务器，将任务 API 暴露为 LLM 可用的工具。

Open task_mcp_server.py and look for FILL_THIS_IN comments. You'll need to:
打开 task_mcp_server.py 并查找 FILL_THIS_IN 注释。你需要：

Task 1.1: Add the Tool Decorator
任务 1.1：添加工具装饰器

The first function needs the decorator that makes it available as an MCP tool.
第一个函数需要添加装饰器，使其作为 MCP 工具可用。

操作说明：为 get_tasks() 添加适当的装饰器


关键概念：MCP 服务器使用装饰器将函数注册为工具。查看文件中其他函数以了解模式。
任务 1.2：实现 GET 请求
完成 get_tasks() 函数，从 API 获取所有任务。
操作说明：
向 tasks 端点发送 HTTP GET 请求
使用 response.raise_for_status() 检查错误
返回 JSON 响应

关键概念：MCP 工具向底层 API 发送 HTTP 请求并返回结果。
任务 1.3：实现 POST 请求
完成 create_task() 函数以创建新任务。
使用函数参数作为 JSON 发送 HTTP POST 请求
包含全部三个参数：title、description、completed
返回 JSON 响应
关键概念：POST 请求在请求体中以 JSON 格式发送数据。
任务 1.4：实现带路径参数的 GET 请求
完成 get_task() 函数，按 ID 获取特定任务。


操作说明：
在路径中包含 task_id 构造 URL
发送 GET 请求
返回 JSON 响应
关键概念：路径参数使用 f-string 包含在 URL 中。
任务 1.5：实现 PUT 请求
完成 update_task() 函数以更新现有任务。


操作说明：
在 URL 路径中包含 task_id
返回 JSON 响应
关键概念：PUT 请求使用部分或完整数据更新资源。
任务 1.6：实现 DELETE 请求
完成 delete_task() 函数以删除任务。

操作说明：
在 URL 路径中包含 task_id 发送 DELETE 请求
返回 JSON 响应
关键概念：你现在已经通过 MCP 工具实现了所有 CRUD 操作！
测试你的 MCP 服务器
完成后，测试你的服务器：

```bash
uv run python task_mcp_server.py
```

The server should start without errors. You won't see much output yet - that's normal. The server is waiting for a client to connect.
服务器应无错误启动。暂时不会看到太多输出——这是正常的。服务器正在等待客户端连接。

第二部分：构建 MCP 客户端

Goal: Create a client that connects to your MCP server, retrieves tools, and enables conversational task management.
目标：创建一个客户端，连接到你的 MCP 服务器，获取工具，并实现对话式任务管理。

Open mcp_cli.py and look for FILL_THIS_IN comments. You'll need to:
打开 mcp_cli.py 并查找 FILL_THIS_IN 注释。你需要：

Task 2.1: Initialize the MCP Client
任务 2.1：初始化 MCP 客户端

Configure the client to connect to your MCP server.
配置客户端以连接到你的 MCP 服务器。

What to do: Create a MultiServerMCPClient with the proper configuration dictionary.
操作说明：使用正确的配置字典创建 MultiServerMCPClient
配置需要包含：

A server name (e.g., "task-manager")
服务器名称（例如 "task-manager"）


传输类型："stdio"

Command：虚拟环境中 Python 解释器的路径
Args：包含 task_mcp_server.py 文件路径的列表

Key concept: MCP clients connect to servers via stdio (standard input/output), launching the server as a subprocess.
关键概念：MCP 客户端通过 stdio（标准输入/输出）连接服务器，将服务器作为子进程启动。

Important: Update the paths to match your environment:
重要：更新路径以匹配你的环境：

command should point to your venv's Python: /path/to/your/venv/bin/python
command 应指向 venv 的 Python：/path/to/your/venv/bin/python

args should contain the full path to task_mcp_server.py
args 应包含 task_mcp_server.py 的完整路径

Task 2.2: Retrieve Tools from Server
任务 2.2：从服务器获取工具

Get the available tools from your MCP server.
从你的 MCP 服务器获取可用工具。

What to do: Call the appropriate async method on the client to fetch tools.
操作说明：调用客户端上适当的 async 方法以获取工具。

Key concept: Tool discovery happens dynamically - the client asks the server what it can do.
关键概念：工具发现是动态的——客户端询问服务器它能做什么。

Task 2.3: Create the Agent
任务 2.3：创建 Agent

Connect the LLM model with the MCP tools.
将 LLM 模型与 MCP 工具连接。

What to do: Use create_agent() to combine the model and tools.
操作说明：使用 create_agent() 组合模型和工具。

Key concept: LangChain agents wrap LLMs with tool-calling capabilities, allowing them to invoke your MCP tools as needed.
关键概念：LangChain Agent 为 LLM 包装工具调用能力，使其能够按需调用你的 MCP 工具。

Task 2.4: Initialize Conversation History
任务 2.4：初始化对话历史

Set up storage for the conversation context.
设置对话上下文的存储。

What to do: Create an empty list to store messages.
操作说明：创建一个空列表来存储消息。

Key concept: Agents are stateless - you must maintain conversation history externally to enable multi-turn conversations.
关键概念：Agent 是无状态的——你必须在外部维护对话历史以支持多轮对话。

Task 2.5: Add User Messages to History
任务 2.5：将用户消息添加到历史

Store user input in the conversation history.
将用户输入存储到对话历史中。

What to do:
操作说明：

Create a HumanMessage with the user's input
使用用户输入创建 HumanMessage

Append it to the messages list
将其追加到 messages 列表

Key concept: Every user message must be added to history before invoking the agent.
关键概念：在调用 Agent 之前，每条用户消息都必须添加到历史中。

Task 2.6: Add Assistant Messages to History
任务 2.6：将助手消息添加到历史

Store the agent's response in the conversation history.
将 Agent 的响应存储到对话历史中。

What to do: Append the assistant's message to the messages list.
操作说明：将助手的消息追加到 messages 列表。

Key concept: Both user and assistant messages go in the history to maintain conversation context.
关键概念：用户和助手的消息都要放入历史中以维持对话上下文。

Test Your Complete Application
测试你的完整应用

Make sure the Task API is still running
确保任务 API 仍在运行

Run your MCP client:
运行你的 MCP 客户端：

```bash
python mcp_client.py
```

Try some commands:
尝试一些命令：

"Create a task to buy groceries"
"创建一个买杂货的任务"

"Show me all my tasks"
"显示我的所有任务"

"Mark the first task as completed"
"将第一个任务标记为已完成"

"Delete the task about groceries"
"删除关于杂货的任务"

Understanding the Data Flow
理解数据流

When you type a message, here's what happens:
当你输入一条消息时，会发生以下过程：

User Input → Your message goes to the LangChain agent
用户输入 → 你的消息发送到 LangChain Agent

Agent Reasoning → The LLM decides which tool(s) to call
Agent 推理 → LLM 决定调用哪些工具

MCP Client → Sends tool requests to your MCP server via stdio
MCP 客户端 → 通过 stdio 向 MCP 服务器发送工具请求

MCP Server → Executes the tool (makes HTTP request to API)
MCP 服务器 → 执行工具（向 API 发送 HTTP 请求）

Task API → Processes the request and returns JSON
任务 API → 处理请求并返回 JSON

Response Chain → Results flow back: API → MCP Server → MCP Client → Agent → User
响应链 → 结果回传：API → MCP 服务器 → MCP 客户端 → Agent → 用户

Each layer has a specific responsibility:
每一层都有特定的职责：

API: Data storage and business logic
API：数据存储和业务逻辑

MCP Server: Tool exposure and HTTP communication
MCP 服务器：工具暴露和 HTTP 通信

MCP Client: Tool discovery and agent orchestration
MCP 客户端：工具发现和 Agent 编排

Agent: Natural language understanding and tool selection
Agent：自然语言理解和工具选择

Common Issues & Debugging Tips
常见问题与调试技巧

"Failed to fetch tasks" Error
"Failed to fetch tasks" 错误

Check that the Task API is running on port 8000
检查任务 API 是否在 8000 端口运行

Verify API_BASE_URL in the MCP server is correct
验证 MCP 服务器中的 API_BASE_URL 是否正确

Ensure you added response.raise_for_status() calls
确保你添加了 response.raise_for_status() 调用

"Connection refused" When Starting Client
启动客户端时出现 "Connection refused"

Update the command path to point to your venv's Python interpreter
更新 command 路径以指向 venv 的 Python 解释器

Update the args path to point to your task_mcp_server.py file
更新 args 路径以指向 task_mcp_server.py 文件

Make sure paths are absolute, not relative
确保路径是绝对路径，而非相对路径

Agent Doesn't Use Tools
Agent 不使用工具

Verify all tools have the @mcp.tool() decorator
验证所有工具都有 @mcp.tool() 装饰器

Check that await client.get_tools() is called
检查是否调用了 await client.get_tools()

Ensure tools are passed to create_agent(model, tools)
确保工具已传递给 create_agent(model, tools)

Conversation Loses Context
对话丢失上下文

Confirm you're adding both HumanMessage and assistant messages to history
确认你将 HumanMessage 和助手消息都添加到了历史中

Verify messages list is passed to agent.ainvoke({"messages": messages})
验证 messages 列表已传递给 agent.ainvoke({"messages": messages})

Check that messages list is initialized before the loop
检查 messages 列表是否在循环之前已初始化

Extension Ideas
扩展想法

Once you've completed the core exercise, try these challenges:
完成核心练习后，尝试以下挑战：

Level 1: Add a Search Tool
级别 1：添加搜索工具

Create a search_tasks(query: str) tool that filters tasks by title or description.
创建 search_tasks(query: str) 工具，按标题或描述过滤任务。

Level 2: Add Due Dates
级别 2：添加截止日期

Extend the MCP server to support the due_date field. Create a tool that lists overdue tasks.
扩展 MCP 服务器以支持 due_date 字段。创建一个列出逾期任务的工具。

Level 3: Multiple Servers
级别 3：多个服务器

Create a second MCP server (e.g., for a calendar API) and connect both to the same client.
创建第二个 MCP 服务器（例如日历 API），并将两者连接到同一客户端。

Level 4: Streaming Responses
级别 4：流式响应

Modify the client to stream the agent's response token-by-token for better UX.
修改客户端，逐 token 流式输出 Agent 响应以改善用户体验。

What You've Learned
你学到了什么

MCP Architecture: You've built a complete three-tier MCP application and understand how each layer communicates.
MCP 架构：你构建了一个完整的三层 MCP 应用，并理解各层如何通信。

Tool Wrapping: You've transformed a REST API into LLM-accessible tools using the MCP protocol.
工具封装：你使用 MCP 协议将 REST API 转换为 LLM 可访问的工具。

Server Development: You've created an MCP server that exposes multiple tools with proper error handling.
服务器开发：你创建了一个 MCP 服务器，暴露多个工具并具备适当的错误处理。

Client Configuration: You've configured an MCP client to discover and use server tools dynamically.
客户端配置：你配置了 MCP 客户端以动态发现和使用服务器工具。

Conversation Management: You've implemented stateful conversations on top of stateless agents.
对话管理：你在无状态 Agent 之上实现了有状态的对话。

Data Flow: You've traced requests from natural language through multiple layers to database operations and back.
数据流：你追踪了从自然语言经多层到数据库操作再返回的请求路径。

Real World Applications
实际应用场景

Development tools: GitHub Copilot, Cursor, and other AI coding assistants use MCP to access codebases, git history, and development tools
开发工具：GitHub Copilot、Cursor 等 AI 编程助手使用 MCP 访问代码库、Git 历史和开发工具

Data analysis platforms: Connect LLMs to databases, analytics APIs, and visualization tools for natural language data exploration
数据分析平台：将 LLM 连接到数据库、分析 API 和可视化工具，实现自然语言数据探索

Customer support systems: Integrate LLMs with CRM systems, knowledge bases, and ticketing platforms
客户支持系统：将 LLM 与 CRM 系统、知识库和工单平台集成

DevOps automation: Let LLMs interact with CI/CD pipelines, monitoring systems, and infrastructure APIs
DevOps 自动化：让 LLM 与 CI/CD 流水线、监控系统和基础设施 API 交互

Research assistants: Connect LLMs to academic databases, data processing tools, and simulation environments
研究助手：将 LLM 连接到学术数据库、数据处理工具和仿真环境

Business intelligence: Enable natural language queries across multiple data sources, reporting tools, and dashboards
商业智能：跨多个数据源、报告工具和仪表板实现自然语言查询
