Expense Tracker Agent


Merge it with your existing deep_atlas environment by installing new dependencies into your original environment.
Create a new virtualenv for this exercise itself using uv sync.
Build an agentic system with tool use and error recovery.



**Implement a SQLite-based storage layer with dynamic queries**
Define tools for LLM function calling using Ollama
Build a multi-turn conversation loop with memory
Implement retry logic for error recovery
Generate structured outputs on demand


Project Goals
**Create an expense tracking assistant that uses Ollama's function calling capabilities to help users manage their expenses through natural conversation. The system maintains conversation context during runtime and persists expense data to SQLite.**

Complete the following goals:
Complete the FILL_THIS_IN sections in storage.py:
Define the SQL schema for the expenses table
Implement parameterized INSERT query
Build dynamic WHERE clauses for filtering
Add error handling for missing records
Complete the FILL_THIS_IN sections in app.py:
Define the tools array with proper function calling schema
Implement tool dispatch logic
Build the retry loop for error recovery
Add a system prompt to initialize conversation
Test your implementation with various scenarios:
Add expenses with different levels of detail
Expense Tracker Agent
开支追踪助手

⚠️ This exercise introduces some new dependencies. Study the included pyproject.toml file and either:
⚠️ 本练习会引入一些新的依赖。请查看附带的 pyproject.toml，并选择以下其一：

Merge it with your existing deep_atlas environment by installing new dependencies into your original environment.
将它合并到你现有的 deep_atlas 环境中，把新依赖安装进原来的环境。

Create a new virtualenv for this exercise itself using uv sync.
或使用 uv sync 为本练习单独创建一个新的虚拟环境。

Build an agentic system with tool use and error recovery.
构建一个支持工具调用与错误恢复的智能体系统。

Objectives:
目标：

Implement a SQLite-based storage layer with dynamic queries.
实现一个基于 SQLite 且支持动态查询的存储层。

Define tools for LLM function calling using Ollama.
使用 Ollama 定义用于 LLM 函数调用的工具。

Build a multi-turn conversation loop with memory.
构建一个带记忆的多轮对话循环。

Implement retry logic for error recovery.
实现用于错误恢复的重试逻辑。

Generate structured outputs on demand.
按需生成结构化输出。

Project Goals
项目目标

Create an expense tracking assistant that uses Ollama's function calling capabilities to help users manage their expenses through natural conversation.
创建一个开支追踪助手，利用 Ollama 的函数调用能力，通过自然对话帮助用户管理开支。

The system maintains conversation context during runtime and persists expense data to SQLite.
系统在运行时维护对话上下文，并将开支数据持久化到 SQLite。

Complete the following goals:
完成以下目标：

 完成 storage.py 中的 FILL_THIS_IN 部分：
 定义 expenses 表的 SQL 架构。
 实现参数化 INSERT 查询。
 构建用于筛选的动态 WHERE 子句。
 为记录不存在的情况添加错误处理。

Complete the FILL_THIS_IN sections in app.py:
完成 app.py 中的 FILL_THIS_IN 部分：

Define the tools array with proper function calling schema.
使用正确的函数调用 schema 定义 tools 数组。
Implement tool dispatch logic.
实现工具分发逻辑。
Build the retry loop for error recovery.
构建用于错误恢复的重试循环。
添加 system prompt 来初始化对话。
用以下不同场景测试你的实现：
添加不同详细程度的开支记录。
使用筛选条件查询开支。
处理需要澄清的模糊请求。

**Trigger errors intentionally**
(invalid dates, missing IDs) to test retry logic
故意触发错误（无效日期、缺失 ID）以测试重试逻辑
Request structured output (e.g., "show me all expenses as JSON").
请求结构化输出（例如：“把所有开支以 JSON 显示”）。

提示
从 storage.py 开始：先让数据库层正常工作。在进入 agent 部分前，先在 Python REPL 中独立测试每个方法。
理解工具 schema：
学习 OpenAI 的函数调用格式。
每个工具都需要 type、function.name、function.description，
以及带正确类型的 function.parameters。

追踪对话流程：
添加 print 语句查看消息何时被追加到 conversation_history。
理解这个顺序（user -> assistant -> tool -> assistant）非常关键。

Test error recovery manually: Before implementing the retry loop, trigger errors and observe what happens. Then design your retry logic accordingly.
手动测试错误恢复：在实现重试循环前，先触发错误并观察现象，再据此设计重试逻辑。

Use parameterized queries: Never use f-strings for SQL queries. Always use ? placeholders with tuple parameters to prevent SQL injection.
使用参数化查询：SQL 查询里不要使用 f-string。始终使用 ? 占位符配合 tuple 参数，以防止 SQL 注入。

Start simple, then enhance: Get basic add/get working first. Then add filters, updates, deletes, and finally error recovery.
先简后繁：先实现基础的 add/get，再加入筛选、更新、删除，最后实现错误恢复。


测试场景
尝试以下对话来验证你的实现：

"I spent $45 on groceries today"
“我今天在杂货上花了 45 美元”

"Show me all my expenses"
“给我看所有开支”

"I spent money on coffee" (ambiguous - should ask for amount)
“我在咖啡上花了钱”（语义不明确，应追问金额）

"Update expense 1 to $50" (tests update logic)
“把第 1 条开支更新为 50 美元”（测试更新逻辑）

"Show me all grocery expenses as JSON" (tests structured output)
“把所有杂货开支以 JSON 显示”（测试结构化输出）

"Delete expense 999" (tests error handling with retries)
“删除开支 999”（测试带重试的错误处理）

Understanding Key Concepts
理解关键概念

Tool calling flow: User message -> LLM decides to call tool -> Tool executes -> Result added to history -> LLM generates final response.
工具调用流程：用户消息 -> LLM 决定调用工具 -> 工具执行 -> 结果写入历史 -> LLM 生成最终回复。

Retry logic: On error -> Append error to history -> Get new LLM response -> Extract corrected tool call -> Try again (up to 3 times).
重试逻辑：发生错误 -> 将错误追加到历史 -> 获取新的 LLM 响应 -> 提取修正后的工具调用 -> 再次尝试（最多 3 次）。

Conversation memory: All messages (user, assistant, tool) stay in conversation_history for the session, giving context for multi-turn interactions.
会话记忆：所有消息（user、assistant、tool）都会保留在会话期内的 conversation_history 中，为多轮交互提供上下文。

Structured outputs: The LLM can format tool results as JSON/CSV when explicitly requested by the user.
结构化输出：当用户明确请求时，LLM 可以将工具结果格式化为 JSON/CSV。

You did it!
你完成了！
