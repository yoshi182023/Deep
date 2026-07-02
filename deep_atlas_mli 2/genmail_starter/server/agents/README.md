# AI Agents

Place your LLM-powered email intelligence features here.

## LangGraph 使用说明

以下模块使用 **LangGraph** 编排工作流（其余功能 1–7 仍为 `chat_completion()` 直连）：

| 文件 | 功能 | LangGraph 结构 |
|------|------|----------------|
| `draft_reply.py` | 8 智能回复 | load → draft → **interrupt** → send |
| `inbox_intelligence.py` | 9 主动收件箱 | **fan-out** 并行 gather×3 → **interrupt** 确认 → report |
| `cross_thread.py` | 10 跨线程综合 | search → synthesize → **reflect** 自检 |

| 路由 | 说明 |
|------|------|
| `POST /ai/draft-reply/*` | 功能 8 HITL |
| `POST /ai/inbox-intelligence` + `/resume` | 功能 9 HITL |
| `POST /ai/synthesize` | 功能 10 一键 invoke 三节点 |

## Suggested Structure

```
agents/
├── summarizer.py          # Thread summarization
├── digest.py              # Unread digest generation
├── classifier.py          # Urgency and thread state classification
├── tracker.py             # Commitment tracking
├── synthesizer.py         # Cross-thread synthesis
├── draft_reply.py         # 【LangGraph】功能 8 智能回复 + HITL
├── inbox_intelligence.py  # 【LangGraph】功能 9 主动收件箱 + HITL
├── cross_thread.py        # 【LangGraph】功能 10 跨线程 search→reflect
└── mcp_server.py          # FastMCP server (if using MCP architecture)
```

## Usage

Import and use in Flask routes:

```python
from agents.summarizer import summarize_thread

@app.route('/ai/summarize/<thread_id>')
def summarize(thread_id):
    summary = summarize_thread(thread_id)
    return jsonify({"summary": summary})
```

Or run as standalone MCP server and connect Flask as MCP client.
