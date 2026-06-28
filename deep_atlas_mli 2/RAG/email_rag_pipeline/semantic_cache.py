"""
Step 6: 语义缓存系统 (Semantic Caching)
基于向量相似度的智能缓存，提高 RAG 系统性能
"""

import os
import json
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv


@dataclass
class CacheEntry:
    """缓存条目"""
    cache_key: str
    query: str
    query_embedding: List[float]
    results: str  # JSON 格式的结果
    metadata: Dict[str, Any]
    created_at: str
    accessed_at: str
    access_count: int


class SemanticCache:
    """语义缓存系统 - 基于向量相似度的智能缓存"""
    
    def __init__(
        self,
        connection_url: str,
        model_name: str = "all-MiniLM-L6-v2",
        cache_ttl: int = 86400,  # 24 小时
        similarity_threshold: float = 0.95
    ):
        """
        初始化语义缓存
        
        Args:
            connection_url: PostgreSQL 连接字符串
            model_name: 嵌入模型名称
            cache_ttl: 缓存过期时间（秒）
            similarity_threshold: 相似度阈值 (0-1)
        """
        self.connection_url = connection_url
        self.model = SentenceTransformer(model_name)
        self.cache_ttl = cache_ttl
        self.similarity_threshold = similarity_threshold
        self.embedding_dim = 384
        
        # 内存缓存（L1）
        self.memory_cache: Dict[str, CacheEntry] = {}
        
        self._connect_db()
        self._init_cache_table()
    
    def _connect_db(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(self.connection_url)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print("✓ 连接到数据库成功")
        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            raise
    
    def _init_cache_table(self):
        """初始化缓存表"""
        try:
            # 创建缓存表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS semantic_cache (
                cache_key TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                query_embedding VECTOR(384),
                results TEXT NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 1
            );
            
            CREATE INDEX IF NOT EXISTS idx_cache_embedding_ivfflat 
            ON semantic_cache USING ivfflat (query_embedding vector_cosine_ops);
            
            CREATE INDEX IF NOT EXISTS idx_cache_accessed_at 
            ON semantic_cache(accessed_at);
            """
            
            for statement in create_table_sql.strip().split(';'):
                if statement.strip():
                    self.cursor.execute(statement)
            
            self.conn.commit()
            print("✓ 缓存表已初始化")
        
        except Exception as e:
            print(f"✗ 初始化缓存表失败: {e}")
            raise
    
    def _generate_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入"""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def _is_cache_expired(self, timestamp_str: str) -> bool:
        """检查缓存是否过期"""
        created_at = datetime.fromisoformat(timestamp_str)
        return datetime.now() - created_at > timedelta(seconds=self.cache_ttl)
    
    def get(
        self,
        query: str,
        use_semantic_match: bool = True
    ) -> Optional[Tuple[str, float, str]]:
        """
        获取缓存结果
        
        Args:
            query: 查询文本
            use_semantic_match: 是否使用语义匹配查找相似查询
            
        Returns:
            (缓存结果, 相似度, 缓存键) 或 None
        """
        cache_key = self._generate_cache_key(query)
        
        # L1: 精确匹配检查（内存缓存）
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not self._is_cache_expired(entry.created_at):
                self._update_access(cache_key)
                return entry.results, 1.0, cache_key
            else:
                del self.memory_cache[cache_key]
        
        # L2: 数据库精确匹配
        try:
            sql = """
            SELECT results, created_at 
            FROM semantic_cache 
            WHERE cache_key = %s
            """
            self.cursor.execute(sql, (cache_key,))
            row = self.cursor.fetchone()
            
            if row:
                if not self._is_cache_expired(row['created_at'].isoformat()):
                    self._update_access(cache_key)
                    return row['results'], 1.0, cache_key
        
        except Exception as e:
            print(f"✗ 数据库查询失败: {e}")
        
        # L3: 语义相似性匹配
        if use_semantic_match:
            query_embedding = self._generate_embedding(query)
            
            try:
                sql = f"""
                SELECT cache_key, query, results, created_at,
                       1 - (query_embedding <=> %s::vector) as similarity
                FROM semantic_cache
                WHERE (1 - (query_embedding <=> %s::vector)) > %s
                  AND created_at > CURRENT_TIMESTAMP - INTERVAL '{self.cache_ttl} seconds'
                ORDER BY similarity DESC
                LIMIT 1
                """
                
                embedding_str = str(query_embedding)
                
                self.cursor.execute(
                    sql,
                    (embedding_str, embedding_str, self.similarity_threshold)
                )
                row = self.cursor.fetchone()
                
                if row and float(row['similarity']) >= self.similarity_threshold:
                    self._update_access(row['cache_key'])
                    return row['results'], float(row['similarity']), row['cache_key']
            
            except Exception as e:
                print(f"✗ 语义缓存查询失败: {e}")
        
        return None
    
    def set(
        self,
        query: str,
        results: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存储缓存结果
        
        Args:
            query: 查询文本
            results: 结果（JSON 字符串）
            metadata: 元数据
            
        Returns:
            缓存键
        """
        cache_key = self._generate_cache_key(query)
        query_embedding = self._generate_embedding(query)
        
        if metadata is None:
            metadata = {}
        
        # 添加缓存统计
        metadata['cached_at'] = datetime.now().isoformat()
        
        try:
            sql = """
            INSERT INTO semantic_cache 
            (cache_key, query, query_embedding, results, metadata, created_at, accessed_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (cache_key) DO UPDATE SET
                results = EXCLUDED.results,
                metadata = EXCLUDED.metadata,
                accessed_at = CURRENT_TIMESTAMP,
                access_count = semantic_cache.access_count + 1
            """
            
            embedding_str = str(query_embedding)
            self.cursor.execute(
                sql,
                (cache_key, query, embedding_str, results, json.dumps(metadata))
            )
            self.conn.commit()
            
            # L1: 也存到内存缓存
            self.memory_cache[cache_key] = CacheEntry(
                cache_key=cache_key,
                query=query,
                query_embedding=query_embedding,
                results=results,
                metadata=metadata,
                created_at=datetime.now().isoformat(),
                accessed_at=datetime.now().isoformat(),
                access_count=1
            )
            
            return cache_key
        
        except Exception as e:
            print(f"✗ 缓存存储失败: {e}")
            raise
    
    def _update_access(self, cache_key: str):
        """更新访问时间和计数"""
        try:
            sql = """
            UPDATE semantic_cache 
            SET accessed_at = CURRENT_TIMESTAMP, 
                access_count = access_count + 1
            WHERE cache_key = %s
            """
            self.cursor.execute(sql, (cache_key,))
            self.conn.commit()
        except Exception as e:
            print(f"✗ 更新访问记录失败: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {}
        
        try:
            # 总缓存项数
            self.cursor.execute("SELECT COUNT(*) as cnt FROM semantic_cache")
            stats['total_entries'] = self.cursor.fetchone()['cnt']
            
            # 总访问次数
            self.cursor.execute("SELECT SUM(access_count) as total FROM semantic_cache")
            result = self.cursor.fetchone()
            stats['total_accesses'] = result['total'] or 0
            
            # 平均访问次数
            self.cursor.execute("SELECT AVG(access_count) as avg FROM semantic_cache")
            result = self.cursor.fetchone()
            stats['avg_accesses'] = round(result['avg'] or 0, 2)
            
            # 最热门的查询
            self.cursor.execute("""
                SELECT query, access_count 
                FROM semantic_cache 
                ORDER BY access_count DESC 
                LIMIT 5
            """)
            stats['top_queries'] = [
                {'query': row['query'], 'count': row['access_count']}
                for row in self.cursor.fetchall()
            ]
            
            # 缓存命中率估计
            if stats['total_entries'] > 0:
                cache_hits = stats['total_accesses'] - stats['total_entries']
                stats['estimated_hit_rate'] = round(
                    cache_hits / stats['total_accesses'] * 100, 2
                ) if stats['total_accesses'] > 0 else 0
            
            return stats
        
        except Exception as e:
            print(f"✗ 获取统计信息失败: {e}")
            return {}
    
    def clear_expired(self) -> int:
        """清除过期缓存"""
        try:
            sql = f"""
            DELETE FROM semantic_cache 
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '{self.cache_ttl} seconds'
            """
            self.cursor.execute(sql)
            self.conn.commit()
            
            deleted = self.cursor.rowcount
            print(f"✓ 清除 {deleted} 条过期缓存")
            return deleted
        
        except Exception as e:
            print(f"✗ 清除过期缓存失败: {e}")
            return 0
    
    def clear_all(self):
        """清除所有缓存"""
        try:
            self.cursor.execute("TRUNCATE semantic_cache")
            self.conn.commit()
            self.memory_cache.clear()
            print("✓ 已清除所有缓存")
        except Exception as e:
            print(f"✗ 清除缓存失败: {e}")
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.cursor.close()
            self.conn.close()
            print("✓ 数据库连接已关闭")


class CachedRetriever:
    """带缓存的检索器"""
    
    def __init__(self, retriever, cache: SemanticCache):
        """
        初始化缓存检索器
        
        Args:
            retriever: 原始检索器
            cache: 语义缓存实例
        """
        self.retriever = retriever
        self.cache = cache
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_time': 0,
            'cache_time': 0,
            'retrieval_time': 0
        }
    
    def search_with_cache(
        self,
        query: str,
        top_k: int = 10,
        use_cache: bool = True
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """
        带缓存的搜索
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            use_cache: 是否使用缓存
            
        Returns:
            (搜索结果, 统计信息)
        """
        self.stats['total_queries'] += 1
        start_time = time.time()
        
        cache_key = None
        similarity = 0.0
        
        # 检查缓存
        if use_cache:
            cache_start = time.time()
            cache_result = self.cache.get(query, use_semantic_match=True)
            cache_time = time.time() - cache_start
            self.stats['cache_time'] += cache_time
            
            if cache_result:
                results_str, similarity, cache_key = cache_result
                results = json.loads(results_str)
                
                self.stats['cache_hits'] += 1
                
                return results, {
                    'source': 'cache',
                    'similarity': similarity,
                    'cache_key': cache_key,
                    'time': cache_time,
                    'hit_rate': round(
                        self.stats['cache_hits'] / self.stats['total_queries'] * 100, 2
                    )
                }
            else:
                self.stats['cache_misses'] += 1
        
        # 执行实际搜索
        retrieval_start = time.time()
        results = self.retriever.search_hybrid(query, top_k=top_k)
        retrieval_time = time.time() - retrieval_start
        self.stats['retrieval_time'] += retrieval_time
        
        # 格式化结果并缓存
        results_data = [
            {
                'email_id': r.email_id,
                'company': r.company,
                'job_title': r.job_title,
                'person_name': r.person_name,
                'contact_info': r.contact_info,
                'similarity_score': r.similarity_score
            }
            for r in results
        ]
        
        if use_cache:
            cache_key = self.cache.set(
                query,
                json.dumps(results_data),
                metadata={
                    'top_k': top_k,
                    'result_count': len(results_data)
                }
            )
        
        total_time = time.time() - start_time
        self.stats['total_time'] += total_time
        
        return results_data, {
            'source': 'retrieval',
            'time': retrieval_time,
            'hit_rate': round(
                self.stats['cache_hits'] / self.stats['total_queries'] * 100, 2
            ),
            'cache_key': cache_key
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total = self.stats['total_queries']
        
        if total == 0:
            return {}
        
        avg_time = self.stats['total_time'] / total
        avg_cache_time = self.stats['cache_time'] / self.stats['cache_hits'] if self.stats['cache_hits'] > 0 else 0
        avg_retrieval_time = self.stats['retrieval_time'] / self.stats['cache_misses'] if self.stats['cache_misses'] > 0 else 0
        
        return {
            'total_queries': total,
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'hit_rate': round(self.stats['cache_hits'] / total * 100, 2),
            'avg_query_time': round(avg_time * 1000, 2),
            'avg_cache_time': round(avg_cache_time * 1000, 2),
            'avg_retrieval_time': round(avg_retrieval_time * 1000, 2),
            'speedup': round(avg_retrieval_time / avg_cache_time, 1) if avg_cache_time > 0 else 0
        }


def benchmark_cache(retriever, cache: SemanticCache, queries: List[str], iterations: int = 3):
    """缓存性能基准测试"""
    
    print("\n" + "="*100)
    print("🔧 缓存系统性能基准测试")
    print("="*100 + "\n")
    
    cached_retriever = CachedRetriever(retriever, cache)
    
    # 预热缓存
    print("预热缓存中...")
    for query in queries:
        cached_retriever.search_with_cache(query, top_k=5)
    
    print(f"\n测试 {len(queries)} 个查询，每个重复 {iterations} 次\n")
    
    for i in range(iterations):
        print(f"第 {i+1} 轮:")
        for query in queries:
            results, info = cached_retriever.search_with_cache(query, top_k=5)
            source = "缓存" if info['source'] == 'cache' else "检索"
            print(f"  '{query[:30]}...' → {source} ({info['time']*1000:.2f}ms)")
    
    # 性能报告
    report = cached_retriever.get_performance_report()
    
    print("\n" + "="*100)
    print("📊 性能报告")
    print("="*100)
    print(f"\n总查询数: {report['total_queries']}")
    print(f"缓存命中: {report['cache_hits']} ({report['hit_rate']:.1f}%)")
    print(f"缓存未中: {report['cache_misses']}")
    print(f"\n平均查询时间: {report['avg_query_time']:.2f}ms")
    print(f"平均缓存查询: {report['avg_cache_time']:.2f}ms")
    print(f"平均检索查询: {report['avg_retrieval_time']:.2f}ms")
    print(f"性能提升: {report['speedup']:.1f}x (缓存比检索快)")
    
    # 缓存统计
    cache_stats = cache.get_statistics()
    print(f"\n缓存统计:")
    print(f"  缓存条数: {cache_stats.get('total_entries', 0)}")
    print(f"  总访问次数: {cache_stats.get('total_accesses', 0)}")
    print(f"  平均访问次数: {cache_stats.get('avg_accesses', 0)}")
    print(f"  热门查询: {len(cache_stats.get('top_queries', []))}")


if __name__ == "__main__":
    # 加载环境变量
    load_dotenv("/workspaces/Deep/.env")
    connection_url = os.getenv("NEON_PG_CONNECTION_URL")
    
    if not connection_url:
        print("✗ 缺少 NEON_PG_CONNECTION_URL 环境变量")
        exit(1)
    
    print("初始化语义缓存系统...")
    cache = SemanticCache(
        connection_url,
        cache_ttl=86400,  # 24 小时
        similarity_threshold=0.95
    )
    
    # 导入检索器
    from retrieval import EmailRetriever
    
    retriever = EmailRetriever(connection_url)
    
    # 测试查询
    test_queries = [
        "Python 工程师招聘",
        "远程工作机会",
        "数据分析职位",
        "全栈开发工作",
        "DevOps 工程师"
    ]
    
    # 运行基准测试
    benchmark_cache(retriever, cache, test_queries, iterations=3)
    
    # 关闭连接
    retriever.close()
    cache.close()
