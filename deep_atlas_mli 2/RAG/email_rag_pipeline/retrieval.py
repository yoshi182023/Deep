"""
Email RAG 检索系统
支持向量语义搜索、全文搜索、混合排序
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


@dataclass
class SearchResult:
    """搜索结果数据类"""
    email_id: str
    sender: str
    date: str
    subject: str
    person_name: str
    company: str
    job_title: str
    contact_info: str
    similarity_score: float  # 0-1, 1 为完全相同
    search_type: str  # "vector" | "fulltext" | "hybrid"
    snippet: str  # 匹配片段预览


class EmailRetriever:
    """Email RAG 检索器"""
    
    def __init__(self, connection_url: str, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化检索器
        
        Args:
            connection_url: PostgreSQL 连接字符串
            model_name: 嵌入模型名称
        """
        self.connection_url = connection_url
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384
        self._connect_db()
    
    def _connect_db(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(self.connection_url)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✓ 连接到数据库成功")
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入"""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def search_by_vector(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        向量语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回前 K 个结果
            threshold: 相似度阈值 (0-1)
            
        Returns:
            搜索结果列表 (按相似度从高到低排序)
        """
        query_embedding = self._generate_embedding(query)
        
        sql = """
        SELECT 
            email_id, sender, email_date, subject, body,
            person_name, company, job_title, contact_info,
            1 - (embedding <=> %s::vector) as similarity
        FROM emails_rag
        WHERE (1 - (embedding <=> %s::vector)) > %s
        ORDER BY similarity DESC
        LIMIT %s
        """
        
        embedding_str = str(query_embedding)
        
        try:
            self.cursor.execute(sql, (embedding_str, embedding_str, threshold, top_k))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                # 生成片段预览 (前 100 字)
                snippet = row['body'][:100].replace('\n', ' ') + "..."
                
                results.append(SearchResult(
                    email_id=row['email_id'],
                    sender=row['sender'],
                    date=row['email_date'],
                    subject=row['subject'],
                    person_name=row['person_name'],
                    company=row['company'],
                    job_title=row['job_title'],
                    contact_info=row['contact_info'],
                    similarity_score=float(row['similarity']),
                    search_type="vector",
                    snippet=snippet
                ))
            
            return results
        
        except Exception as e:
            print(f"✗ 向量搜索失败: {e}")
            return []
    
    def search_by_fulltext(
        self,
        query: str,
        top_k: int = 10,
        search_fields: List[str] = None
    ) -> List[SearchResult]:
        """
        全文搜索
        
        Args:
            query: 查询关键词
            top_k: 返回前 K 个结果
            search_fields: 搜索字段列表
            
        Returns:
            搜索结果列表 (按相关性排序)
        """
        if search_fields is None:
            search_fields = ['subject', 'body', 'company', 'job_title']
        
        # 构建 ILIKE 条件
        conditions = []
        params = []
        for field in search_fields:
            conditions.append(f"{field} ILIKE %s")
            params.append(f"%{query}%")
        
        where_clause = " OR ".join(conditions)
        
        sql = f"""
        SELECT 
            email_id, sender, email_date, subject, body,
            person_name, company, job_title, contact_info
        FROM emails_rag
        WHERE {where_clause}
        LIMIT %s
        """
        
        params.append(top_k)
        
        try:
            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                snippet = row['body'][:100].replace('\n', ' ') + "..."
                
                # 计算匹配分数 (启发式)
                match_count = sum(
                    1 for field in search_fields
                    if query.lower() in row[field].lower()
                )
                relevance = match_count / len(search_fields)
                
                results.append(SearchResult(
                    email_id=row['email_id'],
                    sender=row['sender'],
                    date=row['email_date'],
                    subject=row['subject'],
                    person_name=row['person_name'],
                    company=row['company'],
                    job_title=row['job_title'],
                    contact_info=row['contact_info'],
                    similarity_score=relevance,
                    search_type="fulltext",
                    snippet=snippet
                ))
            
            # 按相关分数排序
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            return results
        
        except Exception as e:
            print(f"✗ 全文搜索失败: {e}")
            return []
    
    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        vector_weight: float = 0.6,
        text_weight: float = 0.4,
        vector_threshold: float = 0.0
    ) -> List[SearchResult]:
        """
        混合搜索 (向量 + 全文)
        
        Args:
            query: 查询文本
            top_k: 返回前 K 个结果
            vector_weight: 向量搜索权重
            text_weight: 全文搜索权重
            vector_threshold: 向量相似度阈值
            
        Returns:
            混合搜索结果 (按综合分数排序)
        """
        # 执行两个搜索
        vector_results = self.search_by_vector(query, top_k=top_k*2, threshold=vector_threshold)
        text_results = self.search_by_fulltext(query, top_k=top_k*2)
        
        # 合并结果 (按 email_id 去重)
        combined = {}
        
        for result in vector_results:
            combined[result.email_id] = {
                'result': result,
                'vector_score': result.similarity_score,
                'text_score': 0
            }
        
        for result in text_results:
            if result.email_id in combined:
                combined[result.email_id]['text_score'] = result.similarity_score
            else:
                combined[result.email_id] = {
                    'result': result,
                    'vector_score': 0,
                    'text_score': result.similarity_score
                }
        
        # 计算混合分数
        ranked = []
        for email_id, data in combined.items():
            hybrid_score = (
                data['vector_score'] * vector_weight +
                data['text_score'] * text_weight
            )
            result = data['result']
            result.similarity_score = hybrid_score
            result.search_type = "hybrid"
            ranked.append(result)
        
        # 按混合分数排序
        ranked.sort(key=lambda x: x.similarity_score, reverse=True)
        return ranked[:top_k]
    
    def search_by_company(
        self,
        company_name: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        按公司名称搜索
        
        Args:
            company_name: 公司名称
            top_k: 返回前 K 个结果
            
        Returns:
            搜索结果列表
        """
        sql = """
        SELECT 
            email_id, sender, email_date, subject, body,
            person_name, company, job_title, contact_info
        FROM emails_rag
        WHERE company ILIKE %s
        ORDER BY email_date DESC
        LIMIT %s
        """
        
        try:
            self.cursor.execute(sql, (f"%{company_name}%", top_k))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                snippet = row['body'][:100].replace('\n', ' ') + "..."
                results.append(SearchResult(
                    email_id=row['email_id'],
                    sender=row['sender'],
                    date=row['email_date'],
                    subject=row['subject'],
                    person_name=row['person_name'],
                    company=row['company'],
                    job_title=row['job_title'],
                    contact_info=row['contact_info'],
                    similarity_score=1.0,  # 完全匹配
                    search_type="company",
                    snippet=snippet
                ))
            
            return results
        
        except Exception as e:
            print(f"✗ 公司搜索失败: {e}")
            return []
    
    def search_by_job_title(
        self,
        job_title: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        按职位搜索
        
        Args:
            job_title: 职位名称
            top_k: 返回前 K 个结果
            
        Returns:
            搜索结果列表
        """
        sql = """
        SELECT 
            email_id, sender, email_date, subject, body,
            person_name, company, job_title, contact_info
        FROM emails_rag
        WHERE job_title ILIKE %s
        ORDER BY email_date DESC
        LIMIT %s
        """
        
        try:
            self.cursor.execute(sql, (f"%{job_title}%", top_k))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                snippet = row['body'][:100].replace('\n', ' ') + "..."
                results.append(SearchResult(
                    email_id=row['email_id'],
                    sender=row['sender'],
                    date=row['email_date'],
                    subject=row['subject'],
                    person_name=row['person_name'],
                    company=row['company'],
                    job_title=row['job_title'],
                    contact_info=row['contact_info'],
                    similarity_score=1.0,
                    search_type="job_title",
                    snippet=snippet
                ))
            
            return results
        
        except Exception as e:
            print(f"✗ 职位搜索失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        stats = {}
        
        # 总邮件数
        self.cursor.execute("SELECT COUNT(*) as cnt FROM emails_rag")
        stats['total_emails'] = self.cursor.fetchone()['cnt']
        
        # 公司数量
        self.cursor.execute("SELECT COUNT(DISTINCT company) as cnt FROM emails_rag WHERE company != ''")
        stats['unique_companies'] = self.cursor.fetchone()['cnt']
        
        # 职位数量
        self.cursor.execute("SELECT COUNT(DISTINCT job_title) as cnt FROM emails_rag WHERE job_title != ''")
        stats['unique_job_titles'] = self.cursor.fetchone()['cnt']
        
        # 日期范围
        self.cursor.execute("SELECT MIN(email_date) as min_d, MAX(email_date) as max_d FROM emails_rag")
        row = self.cursor.fetchone()
        stats['date_range'] = f"{row['min_d']} ~ {row['max_d']}"
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.cursor.close()
            self.conn.close()
            print("✓ 数据库连接已关闭")


def print_results(results: List[SearchResult], max_results: int = 5):
    """格式化打印搜索结果"""
    print(f"\n📧 找到 {len(results)} 条相关邮件\n")
    print("-" * 100)
    
    for i, result in enumerate(results[:max_results], 1):
        print(f"\n{i}. [{result.search_type.upper()}] 相似度: {result.similarity_score:.3f}")
        print(f"   ID: {result.email_id}")
        print(f"   发件人: {result.sender}")
        print(f"   日期: {result.date}")
        print(f"   主题: {result.subject}")
        print(f"   人名: {result.person_name} | 公司: {result.company}")
        print(f"   职位: {result.job_title} | 联系: {result.contact_info}")
        print(f"   预览: {result.snippet}")
    
    if len(results) > max_results:
        print(f"\n... 还有 {len(results) - max_results} 条结果")
    print("\n" + "-" * 100)


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv("/workspaces/Deep/.env")
    connection_url = os.getenv("NEON_PG_CONNECTION_URL")
    
    if not connection_url:
        print("✗ 缺少 NEON_PG_CONNECTION_URL 环境变量")
        exit(1)
    
    # 初始化检索器
    print("初始化检索系统...")
    retriever = EmailRetriever(connection_url)
    
    # 显示数据库统计
    stats = retriever.get_statistics()
    print(f"\n📊 数据库统计:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 示例查询
    print("\n\n" + "="*100)
    print("🔍 搜索示例 1: 向量语义搜索")
    print("="*100)
    query1 = "Python 工程师职位"
    results1 = retriever.search_by_vector(query1, top_k=5)
    print_results(results1)
    
    print("\n" + "="*100)
    print("🔍 搜索示例 2: 全文搜索")
    print("="*100)
    query2 = "recruiter"
    results2 = retriever.search_by_fulltext(query2, top_k=5)
    print_results(results2)
    
    print("\n" + "="*100)
    print("🔍 搜索示例 3: 混合搜索")
    print("="*100)
    query3 = "工程师 招聘"
    results3 = retriever.search_hybrid(query3, top_k=5)
    print_results(results3)
    
    print("\n" + "="*100)
    print("🔍 搜索示例 4: 按公司搜索")
    print("="*100)
    results4 = retriever.search_by_company("RMC", top_k=5)
    print_results(results4)
    
    # 关闭连接
    retriever.close()
