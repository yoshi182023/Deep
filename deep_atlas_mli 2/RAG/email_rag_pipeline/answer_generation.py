"""
Step 7: Answer Generation
RAG pipeline that generates natural-language answers from retrieval results.
"""

# 基于检索结果使用 LLM 生成自然语言答案的 RAG 管道

import os
from typing import List, Dict, Any
from dataclasses import dataclass
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

from retrieval import EmailRetriever
from semantic_cache import SemanticCache, CachedRetriever


@dataclass
class RAGResponse:
    """Complete RAG system response."""
    # RAG 系统完整响应
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    model: str
    retrieved_count: int
    cache_hit: bool


# Original Chinese system prompt (kept for reference):
# 你是一位专业的招聘信息分析助手，专门分析和解答关于招聘邮件的问题。
# 你有访问一个包含 172 封真实招聘邮件的数据库。每封邮件包含：
# - 发件人信息（姓名、公司、职位）
# - 招聘职位详情
# - 联系方式
# - 邮件日期
# **回答规则：**
# 1. 只基于提供的邮件内容回答，不要凭空编造信息
# 2. 如果邮件中没有相关信息，明确告知用户
# 3. 回答要简洁、有条理，使用列表格式展示多个结果
# 4. 引用具体的公司名、联系人、邮件时请标明来源
# 5. 使用中文回答（除非用户用其他语言提问）
SYSTEM_PROMPT = """You are a professional recruiting email analysis assistant.

You have access to a database of 172 real recruiting emails. Each email includes:
- Sender details (name, company, title)
- Job posting details
- Contact information
- Email date

**Response rules:**
1. Answer only from the provided email content; do not invent information
2. If the emails do not contain relevant information, tell the user clearly
3. Keep answers concise and structured; use lists when there are multiple results
4. Cite specific companies, contacts, and email IDs as sources
5. Reply in the same language the user uses in their question

**Response format:**
- Answer the question directly
- Use numbered lists when there are multiple relevant results
- End with "Sources: email_X, email_Y"
"""


class RAGPipeline:
    """Full RAG pipeline: retrieval + cache + answer generation."""
    # 完整的 RAG 管道：检索 + 缓存 + 答案生成

    def __init__(
        self,
        connection_url: str,
        gemini_api_key: str,
        model: str = "gemini-2.0-flash",
        top_k: int = 5,
        cache_ttl: int = 86400,
    ):
        """
        Initialize the RAG pipeline.

        Args:
            connection_url: PostgreSQL connection string
            gemini_api_key: Google Gemini API key
            model: LLM model name
            top_k: Maximum number of emails to retrieve per query
            cache_ttl: Cache TTL in seconds
        """
        self.model = model
        self.top_k = top_k

        # Initialize Gemini client
        self.client = genai.Client(api_key=gemini_api_key)

        # Initialize retriever and cache
        self.retriever = EmailRetriever(connection_url)
        self.cache = SemanticCache(
            connection_url,
            cache_ttl=cache_ttl,
            similarity_threshold=0.95,
        )
        self.cached_retriever = CachedRetriever(self.retriever, self.cache)

        print(f"RAG pipeline ready (model: {model}, top_k: {top_k})")

    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieval results as LLM context."""
        if not results:
            return "(No relevant emails found)"

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"--- Email {i} ({r.get('email_id', 'unknown')}) ---")
            lines.append(f"Company: {r.get('company') or 'Unknown'}")
            lines.append(f"Contact: {r.get('person_name') or 'Unknown'}")
            lines.append(f"Title: {r.get('job_title') or 'Unknown'}")
            lines.append(f"Contact info: {r.get('contact_info') or 'Unknown'}")
            lines.append(f"Relevance: {r.get('similarity_score', 0):.1%}")
            lines.append("")

        return "\n".join(lines)

    def _format_results_for_cache(self, results) -> List[Dict[str, Any]]:
        """Convert SearchResult list to serializable dicts."""
        if not results:
            return []
        # Support both SearchResult dataclass and plain dict formats
        if hasattr(results[0], "email_id"):
            return [
                {
                    "email_id": r.email_id,
                    "company": r.company,
                    "job_title": r.job_title,
                    "person_name": r.person_name,
                    "contact_info": r.contact_info,
                    "similarity_score": r.similarity_score,
                }
                for r in results
            ]
        return results

    def ask(self, question: str, use_cache: bool = True) -> RAGResponse:
        """
        Ask a question and get an answer grounded in email data.

        Args:
            question: User question
            use_cache: Whether to use the semantic cache

        Returns:
            RAGResponse with answer and source metadata
        """
        print(f"\nQuestion: {question}")
        print("Retrieving relevant emails...")

        # 1. Retrieve relevant emails (with cache)
        results, cache_info = self.cached_retriever.search_with_cache(
            question, top_k=self.top_k, use_cache=use_cache
        )
        cache_hit = cache_info["source"] == "cache"

        status = "cache hit" if cache_hit else "retrieval complete"
        print(
            f"   -> {status} ({cache_info['time']*1000:.0f}ms), "
            f"found {len(results)} relevant email(s)"
        )

        # 2. Build LLM prompt
        context = self._format_context(results)
        user_message = f"""Answer the question using the recruiting email data below.

**Retrieved emails:**
{context}

**User question:**
{question}
"""

        # 3. Call Gemini to generate the answer
        print("Generating answer...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=800,
            ),
        )
        answer = response.text

        print(f"\nAnswer:\n{answer}")

        return RAGResponse(
            question=question,
            answer=answer,
            sources=results,
            model=self.model,
            retrieved_count=len(results),
            cache_hit=cache_hit,
        )

    def ask_batch(self, questions: List[str]) -> List[RAGResponse]:
        """
        Ask multiple questions in sequence.

        Args:
            questions: List of questions

        Returns:
            List of RAGResponse objects
        """
        responses = []
        for q in questions:
            resp = self.ask(q)
            responses.append(resp)
            print("\n" + "=" * 80)
        return responses

    def close(self):
        """Close database and cache connections."""
        self.retriever.close()
        self.cache.close()
        print("RAG pipeline closed")


class LocalGeminiRAGPipeline:
    """Gemini LLM + local JSON retrieval (no PostgreSQL required)."""
    # Gemini LLM + 本地 JSON 检索（无需 PostgreSQL）

    def __init__(
        self,
        gemini_api_key: str,
        model: str = "gemini-2.0-flash",
        top_k: int = 5,
    ):
        from local_retrieval import LocalEmailRetriever

        self.model = model
        self.top_k = top_k
        self.client = genai.Client(api_key=gemini_api_key)
        self.retriever = LocalEmailRetriever()
        print(f"Local Gemini RAG pipeline ready (model: {model}, top_k: {top_k})")

    def ask(self, question: str, use_cache: bool = True) -> RAGResponse:
        print(f"\nQuestion: {question}")
        print("Retrieving relevant emails...")

        search_results = self.retriever.search_hybrid(question, top_k=self.top_k)
        results = [
            {
                "email_id": r.email_id,
                "company": r.company,
                "job_title": r.job_title,
                "person_name": r.person_name,
                "contact_info": r.contact_info,
                "similarity_score": r.similarity_score,
            }
            for r in search_results
        ]

        print(f"   -> retrieval complete, found {len(results)} relevant email(s)")

        context_lines = []
        for i, r in enumerate(results, 1):
            context_lines.append(f"--- Email {i} ({r.get('email_id', 'unknown')}) ---")
            context_lines.append(f"Company: {r.get('company') or 'Unknown'}")
            context_lines.append(f"Contact: {r.get('person_name') or 'Unknown'}")
            context_lines.append(f"Title: {r.get('job_title') or 'Unknown'}")
            context_lines.append(f"Contact info: {r.get('contact_info') or 'Unknown'}")
            context_lines.append(f"Relevance: {r.get('similarity_score', 0):.1%}")
            context_lines.append("")

        context = "\n".join(context_lines) if context_lines else "(No relevant emails found)"
        user_message = f"""Answer the question using the recruiting email data below.

**Retrieved emails:**
{context}

**User question:**
{question}
"""

        print("Generating answer...")
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                max_output_tokens=800,
            ),
        )
        answer = response.text

        print(f"\nAnswer:\n{answer}")

        return RAGResponse(
            question=question,
            answer=answer,
            sources=results,
            model=self.model,
            retrieved_count=len(results),
            cache_hit=False,
        )

    def close(self):
        self.retriever.close()
        print("Local Gemini RAG pipeline closed")


def main():
    load_dotenv("/workspaces/Deep/.env")

    connection_url = os.getenv("NEON_PG_CONNECTION_URL")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
        print("Missing GEMINI_API_KEY")
        return

    print("\n" + "=" * 80)
    print("Step 7: RAG Answer Generation")
    print("=" * 80)

    if connection_url:
        print("\nGemini API key detected; using database RAG pipeline\n")
        pipeline = RAGPipeline(
            connection_url=connection_url,
            gemini_api_key=gemini_api_key,
            model="gemini-2.0-flash",
            top_k=5,
        )
    else:
        print("\nGemini API key detected; using local JSON RAG pipeline\n")
        pipeline = LocalGeminiRAGPipeline(
            gemini_api_key=gemini_api_key,
            model="gemini-2.0-flash",
            top_k=5,
        )

    # Sample questions:
    # - 哪些公司正在招聘工程师？
    # - RMC Agency 有哪些职位和联系方式？
    # - 有没有远程工作的招聘信息？
    test_questions = [
        "Which companies are hiring engineers?",
        "What roles and contact details does RMC Agency have?",
        "Are there any remote job postings?",
    ]

    print("=" * 80)
    print("RAG Q&A demo")
    print("=" * 80)

    responses = []
    for question in test_questions:
        print("\n" + "-" * 80)
        resp = pipeline.ask(question)
        responses.append(resp)

    print("\n" + "=" * 80)
    print("Session summary")
    print("=" * 80)
    print(f"Total questions: {len(responses)}")
    print(f"Total emails retrieved: {sum(r.retrieved_count for r in responses)}")
    print(f"Model used: {responses[0].model if responses else 'N/A'}")
    print(f"Cache hits: {sum(1 for r in responses if r.cache_hit)}/{len(responses)}")

    pipeline.close()


if __name__ == "__main__":
    main()
