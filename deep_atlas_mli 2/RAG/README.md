# Building a Production RAG System: Architecture and Best Practices
# 构建生产级 RAG 系统：架构与最佳实践

This guide covers building a Retrieval-Augmented Generation (RAG) system that scales to 100,000+ documents with sub-second response times. We'll follow the pipeline from raw documents to generated answers.
本指南介绍如何构建可扩展到 100,000+ 文档、响应时间低于 1 秒的检索增强生成（RAG）系统。我们将沿着从原始文档到生成答案的流程来讲解。

This document uses Qdrant and Redis as the major components. Adapt the code to similar APIs in your vector database or database system of choice.
本文以 Qdrant 和 Redis 为主要组件。你可以将示例代码调整为你所使用的向量数据库或数据库系统对应的 API。

## Understanding Scale

- 1,000 documents: ~200ms retrieval, manageable costs
- 1,000 篇文档：约 200ms 检索，成本可控
- 10,000 documents: ~2s queries, rising costs
- 10,000 篇文档：约 2s 查询，成本上升
- 100,000 documents: timeouts, 64GB+ memory usage, system failures
- 100,000 篇文档：会出现超时、64GB 以上内存占用以及系统故障

The architecture below addresses these bottlenecks systematically.
下面介绍的架构会系统性地解决这些瓶颈问题。

## Step 1: Document Preprocessing
## 第 1 步：文档预处理

Raw PDF extraction destroys retrieval quality. Implement robust preprocessing before anything else.
原始 PDF 提取会破坏检索质量，因此应当先进行稳健的预处理。

Key points:
关键点：

- Use pdfplumber or similar tools for layout preservation.
- 使用 pdfplumber 或类似工具来保留文档排版结构。
- Extract tables separately to maintain structure.
- 单独提取表格，以保持其结构信息。
- Clean OCR errors before chunking.
- 在分块前清理 OCR 识别错误。
- For complex PDFs, use AWS Textract as a fallback.
- 对于复杂 PDF，可将 AWS Textract 作为备用方案。

## Step 2: Chunking Strategy
## 第 2 步：分块策略

Token-based chunking is fast and consistent, while semantic chunking is slower but more context-aware.
基于 token 的分块速度快且稳定，而语义分块更慢，但更能感知上下文。

- Fixed-size chunking is simple and fast.
- 固定大小分块简单且快速。
- Recursive chunking preserves paragraph and sentence boundaries better.
- 递归分块能更好地保留段落和句子边界。
- Semantic chunking uses embeddings to find topic shifts.
- 语义分块通过 embedding 识别主题转换点。
- Agentic or LLM-based chunking is highly accurate but expensive.
- 基于智能体或大模型的分块精度高，但成本也更高。

## Step 3: Vector Database Setup
## 第 3 步：向量数据库配置

Configure Qdrant for large-scale document storage with memory-efficient settings.
配置 Qdrant 以支持大规模文档存储，并使用内存友好的参数。

Key reasons to choose Qdrant:
选择 Qdrant 的关键原因：

- Open source and flexible.
- 开源且灵活。
- Good quantization support.
- 支持量化，能够显著降低内存占用。
- Strong performance for large-scale retrieval.
- 在大规模检索场景下性能表现良好。

## Step 4: Document Indexing
## 第 4 步：文档索引构建

Index preprocessed and chunked documents into the vector database.
将预处理和分块后的文档索引到向量数据库中。

Best practices:
最佳实践：

- Batch inserts improve ingestion speed.
- 批量插入可以提升导入速度。
- Store complete metadata in the payload.
- 将完整元数据保存在 payload 中。
- Use a consistent embedding model throughout the pipeline.
- 整个流程中使用统一的 embedding 模型。
- Monitor progress for large datasets.
- 对大规模数据集要持续观察处理进度。

## Step 5: Hybrid Retrieval
## 第 5 步：混合检索

Combine multiple retrieval methods for superior accuracy.
结合多种检索方法，以获得更高的准确率。

The hybrid workflow usually includes:
混合检索流程通常包括：

- Dense vector search for semantic recall.
- 稠密向量检索，用于语义召回。
- Sparse keyword search for lexical recall.
- 稀疏关键词检索，用于词汇召回。
- Reciprocal rank fusion to merge candidates.
- 使用倒排秩融合（RRF）合并候选结果。
- Cross-encoder reranking for high precision.
- 使用 Cross-Encoder 进行重排，提升精度。

## Step 6: Semantic Caching
## 第 6 步：语义缓存

Cache results for similar queries to reduce costs and latency.
对相似查询结果进行缓存，可以降低成本并减少延迟。

Key ideas:
核心思路：

- Use cosine similarity thresholds to match similar queries.
- 使用余弦相似度阈值匹配相似查询。
- Store embeddings and results in Redis.
- 将 embedding 和结果存储在 Redis 中。
- Set TTL based on freshness requirements.
- 根据数据新鲜度要求设置 TTL。

## Step 7: Answer Generation
## 第 7 步：答案生成

Generate accurate, cited responses using retrieved context.
使用检索到的上下文生成准确且带引用的回答。

Generation principles:
生成原则：

- Clear, minimal system prompts work best.
- 清晰、简洁的系统提示词效果最好。
- Force citations for every claim.
- 每条结论都要求附带引用。
- Limit context to stay within token budgets.
- 限制上下文长度，以控制 token 消耗。
- Use low temperature for factual accuracy.
- 使用较低的温度参数以保证事实一致性。

## Step 8: Monitoring
## 第 8 步：监控

Track retrieval quality and system performance.
跟踪检索质量和系统性能。

Key metrics to monitor:
需要关注的关键指标：

- Retrieval quality: precision, recall, MRR
- 检索质量：精确率、召回率、MRR
- Latency: per component
- 延迟：按模块统计
- User feedback: thumbs up/down, relevance ratings
- Cost per query


## Implementation Strategy
## 实施策略

- Start small: build with 1,000 documents first.
- 先从小规模开始：先用 1,000 篇文档做原型。
- Measure everything: log retrieval quality, latency, and costs.
- 全部量化：记录检索质量、延迟和成本。
- Scale incrementally: test at 1K, 10K, 50K, and 100K.
- 逐步扩展：依次测试 1K、10K、50K 和 100K 级别。
- Optimize based on monitoring data.
- 根据监控数据进行针对性优化。

Ultimately, focus on user outcomes: fast, accurate answers matter more than the underlying database choice.
最终应以用户体验为中心：快且准的答案比底层数据库选择更重要。
