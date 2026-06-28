"""Local retrieval fallback using precomputed JSON artifacts."""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
from sentence_transformers import SentenceTransformer

from retrieval import SearchResult

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


class LocalEmailRetriever:
    """Retrieve emails from local JSON when PostgreSQL is unavailable."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        records_path = OUTPUT_DIR / "email_records.json"
        embeddings_path = OUTPUT_DIR / "email_embeddings.json"

        if not records_path.is_file() or not embeddings_path.is_file():
            raise FileNotFoundError(
                "本地数据缺失，请确保 output/email_records.json 和 "
                "output/email_embeddings.json 存在，或配置 NEON_PG_CONNECTION_URL"
            )

        with records_path.open(encoding="utf-8") as f:
            records = json.load(f)

        with embeddings_path.open(encoding="utf-8") as f:
            embeddings = json.load(f)

        self.records: Dict[str, dict] = {item["id"]: item for item in records}
        self.embeddings: Dict[str, np.ndarray] = {
            item["id"]: np.asarray(item["embedding"], dtype=np.float32)
            for item in embeddings
        }
        self.model = SentenceTransformer(model_name)
        print(f"✓ 本地检索模式已加载 {len(self.records)} 封邮件")

    def _to_result(self, record: dict, score: float, search_type: str) -> SearchResult:
        body = record.get("body") or ""
        snippet = body[:100].replace("\n", " ") + ("..." if len(body) > 100 else "")
        return SearchResult(
            email_id=record["id"],
            sender=record.get("sender", ""),
            date=record.get("date", ""),
            subject=record.get("subject", ""),
            person_name=record.get("person_name", ""),
            company=record.get("company", ""),
            job_title=record.get("job_title", ""),
            contact_info=record.get("contact_info", ""),
            similarity_score=float(score),
            search_type=search_type,
            snippet=snippet,
        )

    def _cosine_similarity(self, query_vec: np.ndarray, doc_vec: np.ndarray) -> float:
        denom = np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
        if denom == 0:
            return 0.0
        return float(np.dot(query_vec, doc_vec) / denom)

    def search_by_vector(self, query: str, top_k: int = 10, threshold: float = 0.0) -> List[SearchResult]:
        query_vec = np.asarray(self.model.encode(query, convert_to_tensor=False), dtype=np.float32)
        scored = []
        for email_id, doc_vec in self.embeddings.items():
            score = self._cosine_similarity(query_vec, doc_vec)
            if score > threshold and email_id in self.records:
                scored.append(self._to_result(self.records[email_id], score, "vector"))
        scored.sort(key=lambda item: item.similarity_score, reverse=True)
        return scored[:top_k]

    def search_by_fulltext(
        self,
        query: str,
        top_k: int = 10,
        search_fields: List[str] = None,
    ) -> List[SearchResult]:
        if search_fields is None:
            search_fields = ["subject", "body", "company", "job_title"]

        query_lower = query.lower()
        results = []
        for record in self.records.values():
            match_count = sum(
                1
                for field in search_fields
                if query_lower in str(record.get(field, "")).lower()
            )
            if match_count:
                relevance = match_count / len(search_fields)
                results.append(self._to_result(record, relevance, "fulltext"))

        results.sort(key=lambda item: item.similarity_score, reverse=True)
        return results[:top_k]

    def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        vector_weight: float = 0.6,
        text_weight: float = 0.4,
        vector_threshold: float = 0.0,
    ) -> List[SearchResult]:
        vector_results = self.search_by_vector(query, top_k=top_k * 2, threshold=vector_threshold)
        text_results = self.search_by_fulltext(query, top_k=top_k * 2)

        combined: Dict[str, dict] = {}
        for result in vector_results:
            combined[result.email_id] = {
                "result": result,
                "vector_score": result.similarity_score,
                "text_score": 0.0,
            }
        for result in text_results:
            if result.email_id in combined:
                combined[result.email_id]["text_score"] = result.similarity_score
            else:
                combined[result.email_id] = {
                    "result": result,
                    "vector_score": 0.0,
                    "text_score": result.similarity_score,
                }

        ranked = []
        for data in combined.values():
            result = data["result"]
            result.similarity_score = (
                data["vector_score"] * vector_weight + data["text_score"] * text_weight
            )
            result.search_type = "hybrid"
            ranked.append(result)

        ranked.sort(key=lambda item: item.similarity_score, reverse=True)
        return ranked[:top_k]

    def close(self):
        pass
