"""
Step 5: 混合检索系统 (Hybrid Retrieval)
比较和优化向量搜索、全文搜索和混合搜索的性能
"""

import os
import time
import json
from typing import List, Dict, Any, Tuple
from retrieval import EmailRetriever, SearchResult
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np


class HybridRetrievalAnalyzer:
    """混合检索分析器 - 性能对比和优化"""
    
    def __init__(self, connection_url: str):
        """初始化混合检索分析器"""
        self.retriever = EmailRetriever(connection_url)
        self.results_cache = {}
    
    def compare_search_methods(
        self,
        query: str,
        top_k: int = 10,
        iterations: int = 3
    ) -> Dict[str, Any]:
        """
        对比三种搜索方法的性能
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            iterations: 重复查询次数（用于性能测试）
            
        Returns:
            性能对比结果
        """
        print(f"\n{'='*100}")
        print(f"🔍 查询: '{query}'")
        print(f"{'='*100}\n")
        
        results = {
            'query': query,
            'top_k': top_k,
            'methods': {}
        }
        
        # 1. 向量搜索
        print("1️⃣  向量语义搜索...")
        vector_times = []
        vector_results = None
        
        for _ in range(iterations):
            start = time.time()
            vector_results = self.retriever.search_by_vector(query, top_k=top_k)
            vector_times.append(time.time() - start)
        
        results['methods']['vector'] = {
            'avg_time': np.mean(vector_times),
            'min_time': np.min(vector_times),
            'max_time': np.max(vector_times),
            'results_count': len(vector_results),
            'top_3': self._format_results(vector_results[:3])
        }
        
        print(f"   ⏱️  平均耗时: {results['methods']['vector']['avg_time']*1000:.2f}ms")
        print(f"   📊 找到 {len(vector_results)} 条结果")
        self._print_results_summary(vector_results[:3])
        
        # 2. 全文搜索
        print("\n2️⃣  全文关键词搜索...")
        text_times = []
        text_results = None
        
        for _ in range(iterations):
            start = time.time()
            text_results = self.retriever.search_by_fulltext(query, top_k=top_k)
            text_times.append(time.time() - start)
        
        results['methods']['fulltext'] = {
            'avg_time': np.mean(text_times),
            'min_time': np.min(text_times),
            'max_time': np.max(text_times),
            'results_count': len(text_results),
            'top_3': self._format_results(text_results[:3])
        }
        
        print(f"   ⏱️  平均耗时: {results['methods']['fulltext']['avg_time']*1000:.2f}ms")
        print(f"   📊 找到 {len(text_results)} 条结果")
        self._print_results_summary(text_results[:3])
        
        # 3. 混合搜索
        print("\n3️⃣  混合搜索 (向量 60% + 全文 40%)...")
        hybrid_times = []
        hybrid_results = None
        
        for _ in range(iterations):
            start = time.time()
            hybrid_results = self.retriever.search_hybrid(
                query,
                top_k=top_k,
                vector_weight=0.6,
                text_weight=0.4
            )
            hybrid_times.append(time.time() - start)
        
        results['methods']['hybrid'] = {
            'avg_time': np.mean(hybrid_times),
            'min_time': np.min(hybrid_times),
            'max_time': np.max(hybrid_times),
            'results_count': len(hybrid_results),
            'top_3': self._format_results(hybrid_results[:3])
        }
        
        print(f"   ⏱️  平均耗时: {results['methods']['hybrid']['avg_time']*1000:.2f}ms")
        print(f"   📊 找到 {len(hybrid_results)} 条结果")
        self._print_results_summary(hybrid_results[:3])
        
        # 分析结果重叠
        print("\n" + "="*100)
        print("📈 结果分析")
        print("="*100)
        
        vector_ids = set(r.email_id for r in vector_results[:top_k])
        text_ids = set(r.email_id for r in text_results[:top_k])
        hybrid_ids = set(r.email_id for r in hybrid_results[:top_k])
        
        print(f"\n结果集交集分析:")
        print(f"  向量 ∩ 全文: {len(vector_ids & text_ids)}/{top_k}")
        print(f"  向量 ∩ 混合: {len(vector_ids & hybrid_ids)}/{top_k}")
        print(f"  全文 ∩ 混合: {len(text_ids & hybrid_ids)}/{top_k}")
        print(f"  三者交集: {len(vector_ids & text_ids & hybrid_ids)}/{top_k}")
        
        results['overlap_analysis'] = {
            'vector_text': len(vector_ids & text_ids),
            'vector_hybrid': len(vector_ids & hybrid_ids),
            'text_hybrid': len(text_ids & hybrid_ids),
            'all_three': len(vector_ids & text_ids & hybrid_ids)
        }
        
        # 性能对比
        print(f"\n⚡ 性能对比:")
        print(f"  最快: {self._get_fastest_method(results['methods'])} " + 
              f"({min([m['avg_time'] for m in results['methods'].values()])*1000:.2f}ms)")
        print(f"  最慢: {self._get_slowest_method(results['methods'])} " +
              f"({max([m['avg_time'] for m in results['methods'].values()])*1000:.2f}ms)")
        
        self.results_cache[query] = results
        return results
    
    def optimize_weights(
        self,
        query: str,
        vector_weights: List[float] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        优化混合搜索的权重配置
        
        Args:
            query: 查询文本
            vector_weights: 向量权重列表 [0.1, 0.2, ..., 0.9]
            top_k: 返回结果数
            
        Returns:
            不同权重下的性能对比
        """
        if vector_weights is None:
            vector_weights = [0.1, 0.3, 0.5, 0.6, 0.7, 0.9]
        
        print(f"\n{'='*100}")
        print(f"⚙️  权重优化分析: '{query}'")
        print(f"{'='*100}\n")
        
        results = {
            'query': query,
            'weights': {}
        }
        
        for v_weight in vector_weights:
            t_weight = 1.0 - v_weight
            
            hybrid_results = self.retriever.search_hybrid(
                query,
                top_k=top_k,
                vector_weight=v_weight,
                text_weight=t_weight
            )
            
            avg_score = np.mean([r.similarity_score for r in hybrid_results]) if hybrid_results else 0
            
            results['weights'][f"V:{v_weight:.1f}_T:{t_weight:.1f}"] = {
                'vector_weight': v_weight,
                'text_weight': t_weight,
                'avg_score': avg_score,
                'results_count': len(hybrid_results),
                'top_result_score': hybrid_results[0].similarity_score if hybrid_results else 0
            }
            
            print(f"向量权重: {v_weight:.1f} | 全文权重: {t_weight:.1f} " +
                  f"| 平均分: {avg_score:.3f} | 最高分: {hybrid_results[0].similarity_score if hybrid_results else 0:.3f}")
        
        # 找最优权重
        best_weight = max(
            results['weights'].items(),
            key=lambda x: x[1]['avg_score']
        )
        
        print(f"\n✨ 推荐权重: {best_weight[0]} (平均分: {best_weight[1]['avg_score']:.3f})")
        
        return results
    
    def recommendation_system(
        self,
        query: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        推荐系统 - 使用优化的混合搜索返回最佳结果
        
        Args:
            query: 查询文本
            top_k: 返回结果数
            
        Returns:
            排序后的推荐结果
        """
        print(f"\n{'='*100}")
        print(f"🎯 推荐系统: '{query}'")
        print(f"{'='*100}\n")
        
        # 使用优化的权重
        results = self.retriever.search_hybrid(
            query,
            top_k=top_k,
            vector_weight=0.6,
            text_weight=0.4
        )
        
        print(f"📋 为您推荐 {len(results)} 条相关招聘信息:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. 🌟 相关度: {result.similarity_score:.2%}")
            print(f"   公司: {result.company or '未知'} | 职位: {result.job_title or '未知'}")
            print(f"   联系人: {result.person_name} ({result.contact_info})")
            print(f"   主题: {result.subject[:60]}...")
            print()
        
        return results
    
    def _format_results(self, results: List[SearchResult]) -> List[Dict]:
        """格式化结果为字典"""
        return [
            {
                'email_id': r.email_id,
                'score': round(r.similarity_score, 3),
                'company': r.company,
                'job_title': r.job_title
            }
            for r in results
        ]
    
    def _print_results_summary(self, results: List[SearchResult]):
        """打印结果摘要"""
        for i, r in enumerate(results, 1):
            print(f"   {i}. [{r.similarity_score:.3f}] {r.company or '未知'} - {r.job_title or '未知'}")
    
    def _get_fastest_method(self, methods: Dict) -> str:
        """获取最快的方法"""
        return min(methods.items(), key=lambda x: x[1]['avg_time'])[0]
    
    def _get_slowest_method(self, methods: Dict) -> str:
        """获取最慢的方法"""
        return max(methods.items(), key=lambda x: x[1]['avg_time'])[0]
    
    def generate_report(self) -> str:
        """生成混合检索报告"""
        report = []
        report.append("# 混合检索系统性能报告\n")
        
        for query, results in self.results_cache.items():
            report.append(f"## 查询: '{query}'\n")
            
            report.append("### 性能对比\n")
            report.append("| 方法 | 平均耗时 | 最小耗时 | 最大耗时 | 结果数 |")
            report.append("|------|---------|---------|---------|---------|")
            
            for method, metrics in results['methods'].items():
                report.append(
                    f"| {method} | {metrics['avg_time']*1000:.2f}ms | "
                    f"{metrics['min_time']*1000:.2f}ms | {metrics['max_time']*1000:.2f}ms | "
                    f"{metrics['results_count']} |"
                )
            
            report.append("\n### 结果重叠分析\n")
            overlap = results['overlap_analysis']
            report.append(f"- 向量 ∩ 全文: {overlap['vector_text']}")
            report.append(f"- 向量 ∩ 混合: {overlap['vector_hybrid']}")
            report.append(f"- 全文 ∩ 混合: {overlap['text_hybrid']}")
            report.append(f"- 三者交集: {overlap['all_three']}\n")
        
        return "\n".join(report)
    
    def close(self):
        """关闭连接"""
        self.retriever.close()


def main():
    """主程序"""
    # 加载环境变量
    load_dotenv("/workspaces/Deep/.env")
    connection_url = os.getenv("NEON_PG_CONNECTION_URL")
    
    if not connection_url:
        print("✗ 缺少 NEON_PG_CONNECTION_URL 环境变量")
        return
    
    # 初始化分析器
    analyzer = HybridRetrievalAnalyzer(connection_url)
    
    # 测试查询列表
    test_queries = [
        "Python 工程师招聘",
        "远程工作机会",
        "RMC Agency 职位",
        "数据分析师",
        "全栈开发"
    ]
    
    print("\n" + "="*100)
    print("🚀 混合检索系统 (Hybrid Retrieval) - Step 5")
    print("="*100)
    
    # 对比搜索方法
    for query in test_queries[:2]:  # 只演示前两个查询
        results = analyzer.compare_search_methods(query, top_k=5)
    
    # 权重优化分析
    if test_queries:
        print("\n")
        analyzer.optimize_weights(test_queries[0])
    
    # 推荐系统演示
    if test_queries:
        print("\n")
        analyzer.recommendation_system(test_queries[0], top_k=5)
    
    # 生成报告
    report = analyzer.generate_report()
    
    # 保存报告
    report_path = "/workspaces/Deep/deep_atlas_mli 2/RAG/email_rag_pipeline/hybrid_retrieval_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已保存到: {report_path}")
    
    # 关闭连接
    analyzer.close()


if __name__ == "__main__":
    main()
