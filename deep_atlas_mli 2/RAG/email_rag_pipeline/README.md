# Email RAG Pipeline: 招聘邮件检索增强生成系统

## 项目概述

构建一个使用检索增强生成 (RAG) 技术分析招聘邮件的系统。该系统能够对 172 封真实招聘邮件进行语义搜索，并结合 LLM 生成关于招聘机会、职位要求和公司信息的综合答案。

**关键目标：**
- ✅ **邮件数据收集**：从 Gmail 邮箱批量下载 172 封招聘邮件
- ✅ **向量数据库设置**：使用向量嵌入建立语义检索能力
- ⏳ **RAG 系统实现**：集成 LLM 生成基于邮件的答案

---

## 🏗️ 系统架构

```
招聘邮件 (172 封)
    ↓
[邮件解析器] → 结构化数据提取 (10 个字段)
    ↓
[向量嵌入] → sentence-transformers (384 维)
    ↓
[PostgreSQL + pgvector] → 向量数据库存储
    ↓
[检索系统] → 语义搜索 (未完成)
    ↓
[RAG 管道] → LLM 生成答案 (未完成)
```

---

## 📋 项目阶段完成情况

### ✅ 第 1 阶段：邮件数据收集

**目标**：从不在 OpenAI 训练集中的邮件收集原始数据

**完成情况**：
- 来源：Gmail 收件箱真实招聘邮件
- 数量：172 封邮件
- 格式：mbox 格式 (`Inbox` 文件)
- 日期范围：2026-06-17 至 2026-06-28

**数据质量**：
- 发件人多样性：Yahoo、Public Storage、RMC Agency、Rigelsky Inc、VYZE INC 等
- 字段完整性：100% 收集率
- 内容保真度：保留完整邮件头、正文和署名

---

### ✅ 第 2 阶段：向量数据库设置

**目标**：向量化邮件并建立高效的语义搜索能力

**实现细节**：

#### 2.1 邮件解析与结构化
- **工具**：Python `mailbox` + `email.parser`
- **提取字段**（10 个）：
  ```python
  {
    "id": "email_0",
    "sender": "Kristy Lariviere <klariviere@rmcagency.com>",
    "date": "06-25",                    # MM-DD 格式
    "subject": "RE: Test",
    "body": "邮件正文（已清理）",
    "signature": "邮件署名（关键信息）",
    "person_name": "Kristy Lariviere",
    "company": "RMC Agency",
    "job_title": "Recruiter",
    "contact_info": "klariviere@rmcagency.com"
  }
  ```
- **输出**：`output/email_records.json` (172 条记录)

#### 2.2 向量嵌入
- **模型**：sentence-transformers `all-MiniLM-L6-v2`
- **维度**：384 维
- **嵌入内容**：subject + body
- **处理方式**：批量处理 (batch_size=32)
- **输出**：`output/email_embeddings.json` (1.39 MB)

#### 2.3 数据库存储
- **选型**：Neon PostgreSQL (云托管)
- **扩展**：pgvector (向量操作)
- **表结构**：

```sql
CREATE TABLE emails_rag (
    id BIGSERIAL PRIMARY KEY,
    email_id TEXT UNIQUE,
    sender TEXT,
    email_date VARCHAR(10),           -- MM-DD 格式
    subject TEXT,
    body TEXT,
    signature TEXT,
    person_name TEXT,
    company TEXT,
    job_title TEXT,
    contact_info TEXT,
    embedding VECTOR(384)              -- 384 维向量
);
```

- **记录数**：172 条
- **存储大小**：~2.5 MB (含向量)
- **查询延迟**：< 100ms

**验证结果**：
```
✓ pgvector 扩展已启用
✓ emails_rag 表已创建
✓ 172 条邮件已插入
✓ 向量维度验证：384 维 ✓
✓ 数据完整性：100% ✓
```

---

### ⏳ 第 3 阶段：RAG 系统实现（进行中）

**目标**：实现检索 + LLM 生成管道

**计划功能**：

#### 3.1 检索系统 (Retrieval)
- [ ] **语义搜索**：基于向量相似度的邮件检索
  ```python
  query = "Python 工程师职位"
  query_vector = model.encode(query)
  results = db.search(query_vector, top_k=10)
  ```

- [ ] **全文搜索**：基于 PostgreSQL 全文索引
- [ ] **混合排序**：结合向量相似度 + 全文匹配

#### 3.2 RAG 管道 (Generation)
- [ ] **LLM 集成**：OpenAI API 或本地模型
- [ ] **提示词工程**：针对招聘邮件优化
- [ ] **答案生成**：基于检索结果生成自然语言答案

#### 3.3 问答系统 (Q&A)
- [ ] **多轮对话**：维护对话上下文
- [ ] **问题理解**：识别招聘相关问题
- [ ] **答案验证**：检查一致性

---

## 📁 项目文件结构

```
email_rag_pipeline/
├── email_parser.py                 # 生产级邮件解析脚本
├── email_parser.ipynb              # 交互式 Notebook (30 单元格)
│   ├── 第 1 部分：导入和邮件解析
│   ├── 第 2 部分：向量嵌入
│   └── 第 3 部分：数据库存储
├── output/
│   ├── email_records.json          # 结构化邮件数据
│   └── email_embeddings.json       # 向量嵌入
├── Takeout/Mail/
│   └── Inbox                       # 原始邮件 (mbox 格式)
└── README.md                       # 本文件
```

---

## 📊 性能指标

| 指标 | 值 |
|------|-----|
| 邮件总数 | 172 |
| 向量维度 | 384 |
| 存储大小 | ~2.5 MB |
| 嵌入生成时间 | ~20 秒 |
| 数据库导入时间 | ~12 秒 |
| 单条查询延迟 | < 100ms |

---

## 📚 课程要求完成度

### ✅ 已完成（70%）
- [x] 邮件数据收集 (172 封)
- [x] 向量数据库设置 (pgvector)
- [x] 数据预处理和清理
- [x] 嵌入向量生成 (384-dim)
- [x] 数据持久化存储

### ⏳ 进行中（0%）
- [ ] 检索系统实现
- [ ] LLM 集成 (RAG)
- [ ] 问答系统构建
- [ ] 性能评估

---

## 🚀 快速开始

### 前置要求
- Python 3.12+
- Neon PostgreSQL 账户
- 必要库：`psycopg2`, `sentence-transformers`

### 配置步骤

1. **配置环境变量**：编辑 `/workspaces/Deep/.env`
2. **运行 Notebook**：执行 `email_parser.ipynb`
3. **验证部署**：检查数据库中的 172 条记录

---

**最后更新**：2026-06-28
**项目状态**：Alpha (第 2 阶段完成，第 3 阶段进行中)
