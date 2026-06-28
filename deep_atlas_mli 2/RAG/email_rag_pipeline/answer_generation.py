"""
Step 7: 答案生成系统 (Answer Generation)
基于检索结果使用 LLM 生成自然语言答案的 RAG 管道
"""

import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

from retrieval import EmailRetriever, SearchResult
from semantic_cache import SemanticCache, CachedRetriever


@dataclass
class RAGResponse:
    """RAG 系统完整响应"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    model: str
    retrieved_count: int
    cache_hit: bool


SYSTEM_PROMPT = """你是一位专业的招聘信息分析助手，专门分析和解答关于招聘邮件的问题。

你有访问一个包含 172 封真实招聘邮件的数据库。每封邮件包含：
- 发件人信息（姓名、公司、职位）
- 招聘职位详情
- 联系方式
- 邮件日期

**回答规则：**
1. 只基于提供的邮件内容回答，不要凭空编造信息
2. 如果邮件中没有相关信息，明确告知用户
3. 回答要简洁、有条理，使用列表格式展示多个结果
4. 引用具体的公司名、联系人、邮件时请标明来源邮件 ID
5. 使用中文回答（除非用户用其他语言提问）

**回答格式：**
- 直接回答问题
- 如有多个相关结果，用编号列表展示
- 在回答末尾注明"信息来源：email_X, email_Y"
"""


class RAGPipeline:
    """完整的 RAG 管道：检索 + 缓存 + 答案生成"""

    def __init__(
        self,
        connection_url: str,
        gemini_api_key: str,
        model: str = "gemini-2.0-flash",
        top_k: int = 5,
        cache_ttl: int = 86400,
    ):
        """
        初始化 RAG 管道

        Args:
            connection_url: PostgreSQL 连接字符串
            gemini_api_key: Google Gemini API Key
            model: LLM 模型名称
            top_k: 每次检索的最大邮件数量
            cache_ttl: 缓存有效期（秒）
        """
        self.model = model
        self.top_k = top_k

        # 初始化 Gemini 客户端
        self.client = genai.Client(api_key=gemini_api_key)

        # 初始化检索器和缓存
        self.retriever = EmailRetriever(connection_url)
        self.cache = SemanticCache(
            connection_url,
            cache_ttl=cache_ttl,
            similarity_threshold=0.95,
        )
        self.cached_retriever = CachedRetriever(self.retriever, self.cache)

        print(f"✓ RAG 管道初始化完成 (模型: {model}, top_k: {top_k})")

    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """将检索结果格式化为 LLM 上下文"""
        if not results:
            return "（未找到相关邮件）"

        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"--- 邮件 {i} ({r.get('email_id', 'unknown')}) ---")
            lines.append(f"公司: {r.get('company') or '未知'}")
            lines.append(f"联系人: {r.get('person_name') or '未知'}")
            lines.append(f"职位: {r.get('job_title') or '未知'}")
            lines.append(f"联系方式: {r.get('contact_info') or '未知'}")
            lines.append(f"相关度: {r.get('similarity_score', 0):.1%}")
            lines.append("")

        return "\n".join(lines)

    def _format_results_for_cache(self, results) -> List[Dict[str, Any]]:
        """将 SearchResult 列表转换为可序列化字典"""
        if not results:
            return []
        # 支持 SearchResult dataclass 和普通 dict 两种格式
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
        提问并获取基于邮件数据的答案

        Args:
            question: 用户问题
            use_cache: 是否使用缓存

        Returns:
            RAGResponse 包含答案和来源信息
        """
        print(f"\n💬 问题: {question}")
        print("🔍 检索相关邮件...")

        # 1. 检索相关邮件（带缓存）
        results, cache_info = self.cached_retriever.search_with_cache(
            question, top_k=self.top_k, use_cache=use_cache
        )
        cache_hit = cache_info["source"] == "cache"

        print(
            f"   → {'缓存命中' if cache_hit else '检索完成'} ({cache_info['time']*1000:.0f}ms)，"
            f"找到 {len(results)} 封相关邮件"
        )

        # 2. 构建 LLM 提示词
        context = self._format_context(results)
        user_message = f"""请基于以下招聘邮件数据回答问题。

**检索到的相关邮件：**
{context}

**用户问题：**
{question}
"""

        # 3. 调用 Gemini 生成答案
        print("🤖 生成答案中...")
        try:
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
        except Exception as e:
            # API 不可用时降级为模板答案
            print(f"   ⚠️  LLM 调用失败 ({e.__class__.__name__})，降级为模板答案")
            mock = MockRAGPipeline.__new__(MockRAGPipeline)
            sr_list = self.retriever.search_hybrid(question, top_k=self.top_k)
            answer = mock._generate_template_answer(question, sr_list)

        print(f"\n📝 答案:\n{answer}")

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
        批量提问

        Args:
            questions: 问题列表

        Returns:
            RAGResponse 列表
        """
        responses = []
        for q in questions:
            resp = self.ask(q)
            responses.append(resp)
            print("\n" + "=" * 80)
        return responses

    def close(self):
        """关闭连接"""
        self.retriever.close()
        self.cache.close()
        print("✓ RAG 管道已关闭")


# ──────────────────────────────────────────────────────────────────────────────
# 演示模式：无 API Key 时使用本地模板生成答案
# ──────────────────────────────────────────────────────────────────────────────

class MockRAGPipeline:
    """无需 OpenAI API Key 的演示 RAG 管道（基于模板规则生成答案）"""

    def __init__(self, connection_url: str, top_k: int = 5):
        self.top_k = top_k
        self.retriever = EmailRetriever(connection_url)
        print("✓ 演示 RAG 管道初始化完成（Mock 模式，无需 API Key）")

    def ask(self, question: str) -> RAGResponse:
        """使用规则模板生成答案（用于测试，无 API Key 场景）"""
        print(f"\n💬 问题: {question}")
        print("🔍 检索相关邮件...")

        results = self.retriever.search_hybrid(question, top_k=self.top_k)
        result_dicts = [
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

        print(f"   → 找到 {len(results)} 封相关邮件")

        # 模板答案生成
        answer = self._generate_template_answer(question, results)
        print(f"\n📝 答案:\n{answer}")

        return RAGResponse(
            question=question,
            answer=answer,
            sources=result_dicts,
            model="mock-template",
            retrieved_count=len(results),
            cache_hit=False,
        )

    def _generate_template_answer(self, question: str, results: List[SearchResult]) -> str:
        """基于检索结果生成模板式答案"""
        if not results:
            return "根据当前邮件数据库，未找到与您问题相关的招聘信息。"

        # 过滤出有效的公司/职位信息
        valid = [
            r for r in results
            if r.company or r.job_title or r.person_name
        ]

        if not valid:
            return (
                f"找到 {len(results)} 封相关邮件，但邮件中未能提取到结构化的公司或职位信息。\n"
                f"相关邮件 ID：{', '.join(r.email_id for r in results[:3])}"
            )

        lines = [f"根据邮件数据库，找到 {len(valid)} 条相关招聘信息：\n"]
        for i, r in enumerate(valid, 1):
            company = r.company or "未知公司"
            job = r.job_title or "招聘专员"
            person = r.person_name or "招聘负责人"
            contact = r.contact_info or "请查看原始邮件"
            lines.append(
                f"{i}. **{company}**\n"
                f"   联系人：{person}（{job}）\n"
                f"   联系方式：{contact}\n"
                f"   来源：{r.email_id}"
            )

        lines.append(
            f"\n信息来源：{', '.join(r.email_id for r in valid)}"
        )
        return "\n".join(lines)

    def close(self):
        self.retriever.close()
        print("✓ 演示 RAG 管道已关闭")


# ──────────────────────────────────────────────────────────────────────────────
# 主程序
# ──────────────────────────────────────────────────────────────────────────────

def main():
    load_dotenv("/workspaces/Deep/.env")

    connection_url = os.getenv("NEON_PG_CONNECTION_URL")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    if not connection_url:
        print("✗ 缺少 NEON_PG_CONNECTION_URL")
        return

    print("\n" + "=" * 80)
    print("🚀 Step 7: 答案生成系统 (RAG Answer Generation)")
    print("=" * 80)

    # 根据是否有 API Key 选择管道
    use_mock = not gemini_api_key or gemini_api_key == "your_gemini_api_key_here"

    if use_mock:
        print("\n⚠️  未检测到 GEMINI_API_KEY，使用演示模式（Mock RAG）\n")
        pipeline = MockRAGPipeline(connection_url, top_k=5)
    else:
        print(f"\n✓ 检测到 Gemini API Key，使用真实 LLM 模式\n")
        try:
            pipeline = RAGPipeline(
                connection_url=connection_url,
                gemini_api_key=gemini_api_key,
                model="gemini-2.0-flash",
                top_k=5,
            )
        except Exception as e:
            print(f"⚠️  Gemini API 不可用 ({e.__class__.__name__})，自动降级为演示模式\n")
            pipeline = MockRAGPipeline(connection_url, top_k=5)

    # 测试问题集
    test_questions = [
        "哪些公司正在招聘工程师？",
        "RMC Agency 有哪些职位和联系方式？",
        "有没有远程工作的招聘信息？",
    ]

    print("=" * 80)
    print("📧 RAG 问答演示")
    print("=" * 80)

    responses = []
    for question in test_questions:
        print("\n" + "-" * 80)
        resp = pipeline.ask(question)
        responses.append(resp)

    # 输出汇总
    print("\n" + "=" * 80)
    print("📊 会话汇总")
    print("=" * 80)
    print(f"总问题数: {len(responses)}")
    print(f"总检索邮件: {sum(r.retrieved_count for r in responses)}")
    print(f"使用模型: {responses[0].model if responses else 'N/A'}")
    print(f"缓存命中: {sum(1 for r in responses if r.cache_hit)}/{len(responses)}")

    pipeline.close()


if __name__ == "__main__":
    main()
