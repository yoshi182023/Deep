
# GenMail：基于 LLM 的邮件智能分析

为一款可用的邮件客户端添加 AI 功能。
## 目标

- Build LLM-powered analysis features for email data
- 构建基于 LLM 的邮件数据分析功能
- Integrate external LLM APIs with existing REST endpoints
- 将外部 LLM API 与现有 REST 端点集成
- Handle multi-email reasoning and context synthesis
- 处理多封邮件的推理与上下文综合
---


## 项目概览

GenMail 是 Acme Corp 产品经理（pm@acme.com）使用的邮件客户端。


### 现有应用



GenMail 包含：
- 23 封种子邮件，涵盖多个工作线程（产品发布、Bug 报告、设计评审、供应商谈判）
- 完整的 CRUD 操作（阅读、撰写、回复、删除）
- 线程化（按 thread_id 分组的对话）
- 已读/未读状态跟踪
- 带查询过滤的 REST API


**技术栈：**

- 后端：Flask + SQLite（Python）
- 前端：React + TypeScript
- LLM：OpenAI API、Anthropic，或通过 Ollama 本地运行



**可用端点：**


- 数据库操作（CRUD）
- 查询过滤（`GET /emails?is_read=false`、`GET /threads`、`GET /stats`）
- 用于查看/管理邮件的 UI
- 用于创建测试数据的开发工具

**Project Scope:**
**项目范围：**

- 使用现有 API 端点构建 AI 分析功能
- 无需修改数据库 schema
- 前端工作量最小


**快速开始：**

- 安装可选 AI 依赖：`uv pip install -e ".[ai]"`（在 `server/` 目录下执行）
- 或按需安装特定包：`uv pip install openai langgraph fastmcp`
- 将 AI agent 代码放在 `server/agents/` 目录

---


## 任务


根据下方列表构建功能。
功能按难度排序。


**每项功能的要求：**

- 清晰的调用方式（API 端点、CLI 命令或 UI 触发）
- 结构化输出（JSON、格式化文本或可展示数据）
- 能在种子数据上正常运行



## 功能列表
**难度：** 简单
生成对话线程的简洁摘要。
**输入：** 线程 ID
**输出：** 2–3 句摘要
**示例：**

```
线程：phoenix-timeline-001
摘要："David 询问了 Phoenix 发布时间表。Alex 确认了 4 月 15 日的目标，但指出了身份认证集成的风险。David 要求在周五董事会电话会前安排同步会议。"
```
**成功标准：**
- 涵盖关键参与者、主题和决策
- 适用于数据库中的任意线程
- 省略无关细节

### 2. 未读邮件摘要
**Difficulty:** Easy
**难度：** 简单
**Input:** None (fetches unread emails)  
**输入：** 无（自动获取未读邮件）

**Output:** Grouped summaries by sender or thread  
**输出：** 按发件人或线程分组的摘要

**Example:**

**示例：**

```
Unread Digest (7 emails):

From Sarah Chen (2):
- Sprint planning Thursday at 10am
- Needs decision on Mobile v2.0 offline sync

From Mike Johnson (2):
- Weekly support trends (navigation issues spiking)
- URGENT: Initech data sync broken

From Jennifer Walsh (1):
- Competitor Hooli launched AI analytics
```

```
未读摘要（7 封邮件）：

来自 Sarah Chen（2 封）：
- 周四上午 10 点 Sprint 规划
- 需要决定 Mobile v2.0 离线同步方案

来自 Mike Johnson（2 封）：
- 每周支持趋势（导航问题激增）
- 紧急：Initech 数据同步故障

来自 Jennifer Walsh（1 封）：
- 竞争对手 Hooli 发布了 AI 分析功能
```

**Success criteria:**

**成功标准：**

- All unread emails accounted for
- 涵盖所有未读邮件
- Grouped by sender, urgency, or topic
- 按发件人、紧急程度或主题分组
- Highlights items requiring attention
- 突出需要关注的事项



### 3. 发件人主题分析
分析特定发件人的所有邮件并识别主题聚类
**输入：** 邮箱地址
**输出：** 带示例的主题聚类
**示例：**

```
Sender: sarah.chen@acme.com (8 emails)

Topics:
1. Technical decisions (4 emails)
   - Mobile offline sync architecture
   - API refactor results

2. Sprint planning (3 emails)
   - Phoenix punch list prioritization
   - Thursday planning invite

3. Timeline updates (1 email)
   - Option B adds 2 weeks to roadmap
```

```
发件人：sarah.chen@acme.com（8 封邮件）

主题：
1. 技术决策（4 封）
   - Mobile 离线同步架构
   - API 重构结果

2. Sprint 规划（3 封）
   - Phoenix 待办事项优先级
   - 周四规划会议邀请

3. 时间表更新（1 封）
   - 方案 B 使路线图延长 2 周
```




### 4. 统计仪表盘


Generate inbox analytics beyond the basic `/stats` endpoint.

生成超越基础 `/stats` 端点的收件箱分析。

**Input:** None (or optional date range)  
**输入：** 无（或可选日期范围）

**Output:** Statistics about email patterns  
**输出：** 邮件模式统计

**Example:**

**示例：**

```
Inbox Intelligence:

Volume:
- 23 total emails (7 unread)
- 12 threads active
- Busiest day: Jan 26 (4 emails)

People:
- Most frequent: Jennifer Walsh (4 emails)
- Awaiting reply: Mike Johnson, Lisa Thompson

Threads:
- Longest: Phoenix launch (6 emails over 30 days)
- Most recent: Bug escalation (2 hours ago)
```

```
收件箱智能分析：

邮件量：
- 共 23 封邮件（7 封未读）
- 12 个活跃线程
- 最忙的一天：1 月 26 日（4 封邮件）

人员：
- 往来最多：Jennifer Walsh（4 封）
- 等待回复：Mike Johnson、Lisa Thompson

线程：
- 最长：Phoenix 发布（30 天内 6 封邮件）
- 最近：Bug 升级（2 小时前）
```


**成功标准：**

- Goes beyond basic counts
- 超越基础计数
- Identifies patterns
- 识别模式
- Uses the data model effectively
- 有效利用数据模型



### 5. 承诺追踪

扫描已发送邮件并提取对他人的承诺。
**输出：** 带上下文的承诺列表
**示例：**

```
Your Commitments:

1. To David Park (Jan 28):
   "I'll have a full status report for you by Friday"
   Thread: Phoenix launch timeline
   Status: Overdue (Friday was Jan 30)

2. To Marcus Rivera (Jan 8):
   "Can we add a skip option on step 3?"
   Thread: Design review
   Status: Open (question, awaiting response)
```

```
你的承诺：

1. 致 David Park（1 月 28 日）：
   "我会在周五前给你一份完整的状态报告"
   线程：Phoenix 发布时间表
   状态：已逾期（周五为 1 月 30 日）

2. 致 Marcus Rivera（1 月 8 日）：
   "我们能在第 3 步加一个跳过选项吗？"
   线程：设计评审
   状态：开放（问题，等待回复）
```

**Challenges:**

**挑战：**

- Distinguishing "I'll do X" (commitment) from "I could do X" (possibility)
- 区分「我会做 X」（承诺）与「我可以做 X」（可能性）
- Understanding temporal references ("by Friday", "tomorrow")
- 理解时间表述（「周五前」「明天」）
- Detecting implicit vs explicit commitments
- 识别隐式与显式承诺

**成功标准：**

- Catches clear commitments ("I'll send", "I will", "I'll have")
- 捕获明确承诺（「我会发送」「我将」「我会提供」）
- Identifies recipient and deadline (if mentioned)
- 识别收件人和截止日期（如有提及）
- Minimal false positives
- 误报率最低

### 6. 紧急程度分类

**Difficulty:** Hard

**难度：** 困难

Score emails by urgency based on content, sender, and context.

根据内容、发件人和上下文对邮件进行紧急程度评分。

**Input:** Email or thread ID  
**输入：** 邮件或线程 ID

**Output:** Urgency score + reasoning  
**输出：** 紧急程度分数 + 推理说明

**Example:**

**示例：**

```
Email: "URGENT: Data sync issue affecting Initech"
Urgency: HIGH (9/10)

Reasoning:
- Subject line contains "URGENT"
- Mentions customer name (Initech) - key beta customer per other threads
- Sender is Mike (support lead) who rarely escalates
- Sent during business hours (not auto-generated)
- User replied within 17 minutes (fast response pattern)
```





**成功标准：**

- Identifies high-urgency emails in seed data
- 识别种子数据中的高紧急邮件
- Explains reasoning
- 解释推理过程
- Handles false urgency patterns
- 处理虚假紧急模式



### 7. 线程状态分类

**Difficulty:** Hard

**难度：** 困难

Determine the current state of a thread.

判断线程的当前状态。

**Input:** Thread ID  
**输入：** 线程 ID

**Output:** State classification + explanation  
**输出：** 状态分类 + 说明
**示例：**

```
Thread: enterprise-dash-004 (Enterprise dashboard - Globex)

State: BLOCKED - Waiting on Jennifer
Last activity: Jan 14 (13 days ago)

Context:
- Jennifer said "I'll send over their full requirements doc tomorrow" (Jan 14)
- Document hasn't arrived
- You're blocked on scoping until you see their requirements
```

```
线程：enterprise-dash-004（企业仪表盘 - Globex）

状态：阻塞 — 等待 Jennifer
最后活动：1 月 14 日（13 天前）

上下文：
- Jennifer 说「我明天会把完整需求文档发过来」（1 月 14 日）
- 文档尚未收到
- 在看到需求前无法进行范围界定
```


**可能的状态：**


- ACTIVE — 讨论进行中

- WAITING_ON_YOU — 你需要回复

- WAITING_ON_THEM — 等待他人回复

- BLOCKED — 缺少外部输入无法推进

- RESOLVED — 对话已结束

- FYI — 无需操作



**挑战：**

- Requires understanding speech acts (questions, commitments, information)
- 需要理解言语行为（提问、承诺、信息）
- Must track who said what and who owes what
- 必须追踪谁说了什么、谁欠什么
- Silence is ambiguous (resolved? ghosted? waiting?)
- 沉默具有歧义（已解决？被忽视？等待中？）



**成功标准：**

- Classifies thread states in seed data
- 对种子数据中的线程状态进行分类
- Identifies who's blocking progress
- 识别谁在阻碍进展
- Explains the classification
- 解释分类依据



### 8. 智能回复起草


**难度：** 非常困难

Draft contextually appropriate email replies.

起草符合上下文的邮件回复。

**Input:** Email/thread to reply to  
**输入：** 要回复的邮件/线程

**Output:** Draft reply  
**输出：** 回复草稿


**示例：**

```
Replying to: Sarah Chen (Mobile v2.0 sync decision)

Draft:
Subject: Re: Mobile v2.0 offline sync - need decision

Sarah,

Let's go with Option B. I checked with Jennifer—field sales is our biggest expansion play this quarter, and the 500MB storage unlocks that segment.

I'll adjust the roadmap for the 2-week delay and send stakeholder updates today.

Alex
```

```
回复对象：Sarah Chen（Mobile v2.0 同步决策）

草稿：
主题：Re: Mobile v2.0 offline sync - need decision

Sarah，

我们采用方案 B。我和 Jennifer 确认过——现场销售是本季度最大的扩张方向，500MB 存储能解锁该细分市场。

我会根据 2 周延期调整路线图，今天向相关方发送更新。

Alex
```

**Challenges:**

**挑战：**

- Must match communication style (analyze past emails)
- 必须匹配沟通风格（分析过往邮件）
- Needs to reference correct context (other threads, previous commitments)
- 需要引用正确上下文（其他线程、先前承诺）
- Tone varies by recipient relationship
- 语气因收件人关系而异
- Must avoid repeating what's already been said
- 必须避免重复已说过的内容
- Should answer questions asked
- 应回答所提问题

**Success criteria:**

**成功标准：**

- Replies feel natural
- 回复自然流畅
- References appropriate context from the thread
- 引用线程中的适当上下文
- Matches tone of recipient relationship
- 匹配与收件人的关系语气
- Could be sent with minor edits only
- 仅需少量修改即可发送



### 9. 主动收件箱提醒

**Difficulty:** Very Hard
用户打开应用时自动呈现需要关注的事项。
**输入：** 无（自动运行）
**输出：** 优先级排序的行动列表
**示例：**

```
Inbox Intelligence (unprompted):

🔴 Needs Your Response (2):
1. Mike: Initech data sync issue (sent 2 hours ago)
   Why: Urgent, mentions customer, Mike is waiting

2. Lisa: Phoenix marketing plan (sent yesterday)
   Why: Asked you a direct question about beta customers

⏳ Commitments Due (1):
1. You told David you'd send a status report by Friday
   Thread: Phoenix timeline
   Status: Due today

⚠️ Stalled Conversations (1):
1. Jennifer said she'd send Globex requirements "tomorrow" (Jan 14)
   That was 13 days ago. Follow up?
```

```
收件箱智能（主动）：

🔴 需要你回复（2）：
1. Mike：Initech 数据同步问题（2 小时前发送）
   原因：紧急、提及客户、Mike 在等待

2. Lisa：Phoenix 营销计划（昨天发送）
   原因：直接询问你关于 beta 客户的问题

⏳ 到期承诺（1）：
1. 你告诉 David 会在周五前发送状态报告
   线程：Phoenix 时间表
   状态：今天到期

⚠️ 停滞对话（1）：
1. Jennifer 说她会在「明天」发送 Globex 需求（1 月 14 日）
   距今已 13 天。需要跟进？
```

**Challenges:**

**挑战：**

- Combines multiple features (urgency, commitments, thread state)
- 组合多项功能（紧急程度、承诺、线程状态）
- Must rank/prioritize intelligently
- 必须智能排序/优先级
- Needs to understand causality
- 需要理解因果关系
- Should minimize noise
- 应尽量减少噪音

**Success criteria:**

**成功标准：**

- Surfaces items requiring attention
- 呈现需要关注的事项
- Minimal false positives
- 误报率最低
- Explains reasoning for each item
- 解释每项的推理依据
- Runs autonomously
- 自主运行

### 10. Cross-Thread Synthesizer

### 10. 跨线程综合

**Difficulty:** Very Hard

**难度：** 非常困难

查找提及某主题的所有邮件并跨线程综合洞察。
**输入：** 主题或关键词

**Output:** Synthesis report  
**输出：** 综合报告

**Example:**

**示例：**

```
Topic: "Phoenix"

Phoenix Launch - Cross-Thread Synthesis:

Timeline:
- Target launch: April 15 (per David thread, Dec 28)
- Risk: 2-week delay possible due to Mobile v2.0 decision (per Sarah thread)
- Current status: 75% complete (per Jan 26 update to David)

Key Decisions:
- Design approved (Marcus, Jan 8)
- Mobile offline went with Option B (Sarah, Jan 3)
- Top 3 features for marketing: customizable widgets, real-time collab, new API

Blockers:
- Auth system integration edge cases (Sarah's team working it)
- Initech data sync issue could affect beta testimonial

People Involved:
- David (exec sponsor), Sarah (eng lead), Marcus (design), Jennifer (sales), Lisa (marketing)
```

```
主题："Phoenix"

Phoenix 发布 — 跨线程综合：

时间表：
- 目标发布：4 月 15 日（David 线程，12 月 28 日）
- 风险：Mobile v2.0 决策可能导致 2 周延期（Sarah 线程）
- 当前状态：75% 完成（1 月 26 日给 David 的更新）

关键决策：
- 设计已批准（Marcus，1 月 8 日）
- Mobile 离线采用方案 B（Sarah，1 月 3 日）
- 营销三大功能：可定制组件、实时协作、新 API

阻碍：
- 身份认证系统集成边界情况（Sarah 团队处理中）
- Initech 数据同步问题可能影响 beta 客户证言

相关人员：
- David（执行赞助人）、Sarah（工程负责人）、Marcus（设计）、Jennifer（销售）、Lisa（营销）
```

**Challenges:**

**挑战：**

- Must identify related threads even without shared keywords
- 即使没有共同关键词也要识别相关线程
- Requires understanding themes across disparate conversations
- 需要理解分散对话中的主题
- Needs to synthesize timeline, decisions, blockers coherently
- 需要连贯综合时间表、决策、阻碍
- Avoiding contradictions or outdated info
- 避免矛盾或过时信息

**Success criteria:**

**成功标准：**

- Finds all relevant threads for the topic
- 找到主题的所有相关线程
- Synthesizes information coherently
- 连贯综合信息
- Identifies connections between threads
- 识别线程间联系
- Highlights current state
- 突出当前状态

---

## Implementation Guidance

## 实现指南

### Architecture Options

### 架构选项

**Option 1: API Server Extension**

**选项 1：API 服务器扩展**

- Add `ai/` directory to Flask app
- 在 Flask 应用中添加 `ai/` 目录
- New endpoints like `POST /ai/summarize`, `GET /ai/digest`
- 新端点如 `POST /ai/summarize`、`GET /ai/digest`
- Call GenMail API + LLM, return results
- 调用 GenMail API + LLM，返回结果

**Option 2: Separate Agent Service**

**选项 2：独立 Agent 服务**

- Standalone Python service that talks to GenMail API
- 与 GenMail API 通信的独立 Python 服务
- CLI tool or separate web service
- CLI 工具或独立 Web 服务
- Allows experimentation with frameworks
- 便于使用不同框架进行实验

**Option 3: MCP Server Architecture**

**选项 3：MCP 服务器架构**

- Package AI features as MCP tools using FastMCP
- 使用 FastMCP 将 AI 功能打包为 MCP 工具
- Upgrade Flask app to MCP client
- 将 Flask 应用升级为 MCP 客户端
- Tools exposed via MCP protocol for reusability
- 通过 MCP 协议暴露工具以实现复用
- Enables integration with other MCP-compatible clients
- 支持与其他 MCP 兼容客户端集成

**Option 4: Jupyter Notebook**

**选项 4：Jupyter Notebook**

- Prototyping and exploratory analysis
- 原型开发与探索性分析
- Call API, process with LLM, visualize results
- 调用 API、用 LLM 处理、可视化结果

### Implementation Frameworks

### 实现框架

**Agent Orchestration:**

**Agent 编排：**

- [LangGraph](https://langchain-ai.github.io/langgraph/) — Build agent workflows with state management and cycle visualization
- [LangGraph](https://langchain-ai.github.io/langgraph/) — 构建带状态管理和循环可视化的 agent 工作流
- [LangChain](https://python.langchain.com/) — Agent orchestration and tool composition
- [LangChain](https://python.langchain.com/) — Agent 编排与工具组合
- Useful for features requiring multi-step reasoning (e.g., Cross-Thread Synthesizer, Proactive Inbox Surface)
- 适用于需要多步推理的功能（如跨线程综合、主动收件箱提醒）

**MCP Protocol:**

**MCP 协议：**

- [FastMCP](https://github.com/jlowin/fastmcp) — Package AI features as MCP tools
- [FastMCP](https://github.com/jlowin/fastmcp) — 将 AI 功能打包为 MCP 工具
- Exposes email intelligence as reusable tools via Model Context Protocol
- 通过 Model Context Protocol 将邮件智能暴露为可复用工具
- Flask app can become MCP client to consume these tools
- Flask 应用可作为 MCP 客户端消费这些工具

**Structured Outputs:**

**结构化输出：**

- [Instructor](https://github.com/jxnl/instructor) — Parse LLM responses into typed objects
- [Instructor](https://github.com/jxnl/instructor) — 将 LLM 响应解析为类型化对象
- Useful for classification tasks and JSON schemas
- 适用于分类任务和 JSON schema

### LLM Implementation Notes

### LLM 实现说明

**Prompting:**

**提示词：**

- Specify output format (JSON recommended)
- 指定输出格式（推荐 JSON）
- Show examples in prompts
- 在提示词中展示示例
- For classification tasks, enumerate all possible categories
- 分类任务需枚举所有可能类别
- For summarization, specify length and focus
- 摘要任务需指定长度和重点

**Function Calling:**

**函数调用：**

- Define tools for GenMail API operations
- 为 GenMail API 操作定义工具
- Let the LLM decide which emails to fetch
- 让 LLM 决定获取哪些邮件
- Chain multiple API calls for complex features
- 复杂功能可链式调用多个 API

**Context Management:**

**上下文管理：**

- Long threads may exceed context limits—summarize incrementally
- 长线程可能超出上下文限制——可增量摘要
- For cross-thread features, fetch threads separately and aggregate
- 跨线程功能可分别获取线程再聚合
- Consider caching LLM responses for repeated queries
- 重复查询可考虑缓存 LLM 响应

**Error Handling:**

**错误处理：**

- LLMs hallucinate—verify claims against email data
- LLM 会产生幻觉——对照邮件数据验证主张
- Handle cases where no emails match criteria
- 处理无匹配邮件的情况
- Gracefully degrade when context is insufficient
- 上下文不足时优雅降级

### Testing

### 测试

- Test on seed data first
- 先在种子数据上测试
- Use "Mock Email" dev control to create test scenarios
- 使用「Mock Email」开发控件创建测试场景
- Test edge cases (empty inbox, single-email threads, overdue commitments)
- 测试边界情况（空收件箱、单邮件线程、逾期承诺）
- Compare LLM output to manual identification
- 将 LLM 输出与人工识别结果对比

### Logging and Evaluation

### 日志与评估

**Logging:**

**日志：**

- Log all LLM interactions (prompts, responses, timestamps)
- 记录所有 LLM 交互（提示词、响应、时间戳）
- Track token usage and latency per feature
- 按功能追踪 token 用量和延迟
- Record feature invocations with input parameters and outputs
- 记录功能调用及输入参数与输出
- Store logs in structured format (JSON, SQLite, or log files)
- 以结构化格式存储日志（JSON、SQLite 或日志文件）
- Useful for debugging hallucinations and performance issues
- 便于调试幻觉和性能问题

**Evaluation Frameworks:**

**评估框架：**

- [RAGAS](https://docs.ragas.io/) — RAG evaluation metrics (context relevance, faithfulness, answer correctness)
- [RAGAS](https://docs.ragas.io/) — RAG 评估指标（上下文相关性、忠实度、答案正确性）
- [OpenAI Evals](https://github.com/openai/evals) — Framework for evaluating LLM outputs against expected results
- [OpenAI Evals](https://github.com/openai/evals) — 将 LLM 输出与预期结果对比的评估框架
- [DeepEval](https://github.com/confident-ai/deepeval) — LLM evaluation with custom metrics and test cases
- [DeepEval](https://github.com/confident-ai/deepeval) — 带自定义指标和测试用例的 LLM 评估


**评估策略：**

- Create ground truth datasets from seed emails (manually label urgency, thread states, commitments)
- 从种子邮件创建真值数据集（人工标注紧急程度、线程状态、承诺）
- Measure accuracy, precision, recall for classification tasks
- 分类任务测量准确率、精确率、召回率
- Use LLM-as-judge for subjective tasks (reply quality, summary coherence)
- 主观任务使用 LLM 作为评判（回复质量、摘要连贯性）
- Track false positives and false negatives
- 追踪误报和漏报
- Document failure patterns and root causes
- 记录失败模式及根因

**Metrics to Track:**

**需追踪的指标：**

- Accuracy per feature (% correct on test set)
- 每项功能准确率（测试集正确百分比）
- Latency (time from request to response)
- 延迟（请求到响应的时间）
- Cost (tokens consumed per feature invocation)
- 成本（每次功能调用的 token 消耗）
- Hallucination rate (verifiable claims that are incorrect)
- 幻觉率（可验证但不正确的主张）

### Implementation Requirements

### 实现要求

Features should:

功能应：

- Work reliably on seed data
- 在种子数据上可靠运行
- Provide explainable decisions
- 提供可解释的决策
- Handle errors gracefully
- 优雅处理错误

### Deliverables

### 交付物

- Working code that runs on GenMail
- 可在 GenMail 上运行的代码
- Demo video or live demo
- 演示视频或现场演示
- Writeup (1-2 pages):
- 书面报告（1–2 页）：
  - Features built
  - 已实现的功能
  - Challenges and solutions
  - 挑战与解决方案
  - One failure case and root cause
  - 一个失败案例及根因
  - Potential next steps
  - 潜在后续步骤

### 评估标准

- Feature quality
- 功能质量
- Problem complexity
- 问题复杂度
- Failure analysis
- 失败分析
- Implementation polish
- 实现完成度

**Bonus credit:**

**加分项：**

- Depth over breadth on complex features
- 复杂功能注重深度而非广度
- Edge case handling
- 边界情况处理
- Explainability (showing reasoning)
- 可解释性（展示推理过程）
- Creating test scenarios that expose edge cases
- 创建能暴露边界情况的测试场景

### Resources

### 资源

**LLM APIs:**

**LLM API：**

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [Ollama](https://ollama.ai/) — Run models locally
- [Ollama](https://ollama.ai/) — 本地运行模型

**Agent Frameworks:**

**Agent 框架：**

- [LangGraph](https://langchain-ai.github.io/langgraph/) — State-based agent workflows with visualization
- [LangGraph](https://langchain-ai.github.io/langgraph/) — 带可视化的基于状态的 agent 工作流
- [LangChain](https://python.langchain.com/) — Agent orchestration and tool composition
- [LangChain](https://python.langchain.com/) — Agent 编排与工具组合
- [FastMCP](https://github.com/jlowin/fastmcp) — Build MCP servers in Python
- [FastMCP](https://github.com/jlowin/fastmcp) — 用 Python 构建 MCP 服务器
- [Instructor](https://github.com/jxnl/instructor) — Structured outputs from LLMs
- [Instructor](https://github.com/jxnl/instructor) — 从 LLM 获取结构化输出

**Evaluation:**

**评估：**

- [RAGAS](https://docs.ragas.io/) — RAG and retrieval evaluation
- [RAGAS](https://docs.ragas.io/) — RAG 与检索评估
- [OpenAI Evals](https://github.com/openai/evals) — LLM evaluation framework
- [OpenAI Evals](https://github.com/openai/evals) — LLM 评估框架
- [DeepEval](https://github.com/confident-ai/deepeval) — LLM testing and metrics
- [DeepEval](https://github.com/confident-ai/deepeval) — LLM 测试与指标

**GenMail API:**

**GenMail API：**

- See `CLAUDE.md` for complete endpoint documentation
- 完整端点文档见 `CLAUDE.md`
- All endpoints return JSON
- 所有端点返回 JSON
- Use `GET /emails?is_read=false` for filtered queries
- 使用 `GET /emails?is_read=false` 进行过滤查询
- Use `GET /threads` for thread metadata
- 使用 `GET /threads` 获取线程元数据

### Notes

### 说明

Email communication involves ambiguity, implicit meaning, and context-dependent interpretation.

邮件沟通涉及歧义、隐含含义和依赖上下文的解读。

LLM-powered features will have failure cases.

基于 LLM 的功能必然会出现失败案例。

Understanding failure modes and documenting limitations is part of the implementation process.

理解失败模式并记录局限性是实现过程的一部分。

---

## Frontend: React + TypeScript + Vite

## 前端：React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

此模板提供了一个最小化配置，使 React 能在 Vite 中运行，并支持 HMR 以及一些 ESLint 规则。

Currently, two official plugins are available:

目前有两个官方插件可用：

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) 使用 [Babel](https://babeljs.io/)（在 [rolldown-vite](https://vite.dev/guide/rolldown) 中则使用 [oxc](https://oxc.rs)）来实现 Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) 使用 [SWC](https://swc.rs/) 来实现 Fast Refresh

## React Compiler

## React 编译器

The React Compiler is not enabled on this template because of its impact on dev & build performances.

由于 React 编译器会影响开发与构建性能，此模板默认未启用它。

To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

若要启用，请参阅[此文档](https://react.dev/learn/react-compiler/installation)。

## Expanding the ESLint configuration

## 扩展 ESLint 配置

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

如果你正在开发生产级应用，我们建议更新配置以启用类型感知的 lint 规则：

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // 其他配置...

      // Remove tseslint.configs.recommended and replace with this
      // 移除 tseslint.configs.recommended，并替换为以下内容
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      // 或者，使用此项以获得更严格的规则
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      // 可选：添加此项以获得风格类规则
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
      // 其他配置...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
      // 其他选项...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

你也可以安装 [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) 和 [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom)，以使用 React 专用的 lint 规则：

```js
// eslint.config.js
// ESLint 配置文件
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // 其他配置...
      // Enable lint rules for React
      // 启用 React 的 lint 规则
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      // 启用 React DOM 的 lint 规则
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
      // 其他选项...
    },
  },
])
```
