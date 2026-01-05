# retrieval.py
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import VECTORSTORE_ROOT, EMBEDDING_API_URL, EMBEDDING_MODEL_NAME, DATA_FILES
from typing import List, Dict, Optional, Union
import os
VECTORSTORE_ROOT=""

DATA_FILES = {
    "ICD-10-fix": "../../node_index/merge_path.jsonl",
}
# 全局嵌入模型（共享）
_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL_NAME,
            base_url=EMBEDDING_API_URL,
            api_key="none",
            check_embedding_ctx_length=False,
        )
    return _embeddings


class ICDRetriever:
    """
    ICD 向量检索器（支持单 source / 多 source / 全量检索）
    """
    def __init__(self, sources: Optional[Union[str, List[str]]] = None, k: int = 5):
        if sources is None:
            self.sources = list(DATA_FILES.keys())
        elif isinstance(sources, str):
            self.sources = [sources]
        else:
            self.sources = sources

        self.k = k
        self.vectorstores = {} #向量数据库字典
        self._load_vectorstores()

    def _load_vectorstores(self):
        """惰性加载指定的向量库"""
        for source in self.sources:
            persist_dir = os.path.join(VECTORSTORE_ROOT, source)
            if not os.path.exists(persist_dir):
                print(f"⚠️  向量库不存在: {persist_dir}（跳过）")
                continue

            try:
                self.vectorstores[source] = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=get_embeddings(),
                    collection_metadata={"hnsw:space": "cosine"}  # ✅ 保持一致：余弦相似度
                )
            except Exception as e:
                print(f"❌ 加载 {source} 失败: {e}")

        if not self.vectorstores:
            raise ValueError("没有可用的向量库，请先运行 ingest.py")

    def retrieve(self, query: str, k: Optional[int] = None, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        执行检索
        :param query: 查询文本
        :param k: 返回结果数
        :param filter_dict: 可选，覆盖初始化时的过滤条件
        """
        k = k or self.k
        filter_to_use = filter_dict if filter_dict else None
        all_results = []

        for source, vectorstore in self.vectorstores.items():
            try:
                # ✅ 传入 filter 参数
                results = vectorstore.similarity_search_with_score(
                    query,
                    k=k,
                    filter=filter_to_use  # ← 关键修改！
                )
                for doc, distance in results:
                    similarity = 1 - distance # 1-距离就是相似度
                    all_results.append({
                        "code": doc.metadata["code"],
                        "name": doc.metadata["name"],
                        "source": source,
                        "score": distance,
                        "base_info": doc.page_content,
                        "similarity": similarity
                    })
            except Exception as e:
                print(f"❌ {source} 检索失败: {e}")

        # 排序 + 去重
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        seen_codes, unique_results = set(), []
        for item in all_results:
            if item["code"] not in seen_codes:
                seen_codes.add(item["code"])
                unique_results.append(item)

        return unique_results[:k]

    def hybrid_search(self, query: str, k: Optional[int] = None, alpha: float = 0.5) -> List[Dict]:
        """混合检索（预留接口）"""
        return self.retrieve(query, k)

    def get_stats(self) -> Dict:
        """获取库统计信息"""
        stats, total_docs = {}, 0
        for source, vectorstore in self.vectorstores.items():
            try:
                count = vectorstore._collection.count()
                stats[source] = count
                total_docs += count
            except:
                stats[source] = "unknown"
        stats["total"] = total_docs
        return stats
    
    # 新增的函数方法
    def get_by_id(self, code: str) -> Optional[Dict]:
        """通过 code 直接获取一条item"""
        for source, vectorstore in self.vectorstores.items():
            try:
                result = vectorstore.get(where={"code": code}, limit=1)
                if result and result['metadatas']:
                    return result['metadatas'][0]
            except Exception as e:
                print(f"❌ 在 {source} 中通过ID获取失败: {e}")
        return None
    
    
    def count(self, filter_dict: Dict) -> int:
        """根据filter过滤条件统计item数量"""
        total_count = 0
        for source, vectorstore in self.vectorstores.items():
            try:
                results = vectorstore.get(where=filter_dict, include=[]) # include=[] 表示只获取id，提高效率
                total_count += len(results.get('ids', []))
            except Exception as e:
                print(f"❌ 在 {source} 中统计数量失败: {e}")
        return total_count
    
    def get_all_by_filter(self, filter_dict: Dict) -> List[Dict]:
        """根据 filter 获取所有匹配的item"""
        all_items = []
        seen_codes = set()
        for source, vectorstore in self.vectorstores.items():
            try:
                # ChromaDB 的 get 方法有上限，需要分批获取
                offset = 0
                limit = 1000 # 每次获取1000条
                while True:
                    results = vectorstore.get(where=filter_dict, limit=limit, offset=offset, include=["metadatas"])
                    if not results or not results['metadatas']:
                        break
                    
                    for meta in results['metadatas']:
                        if meta['code'] not in seen_codes:
                            all_items.append(meta)
                            seen_codes.add(meta['code'])
                    
                    if len(results['metadatas']) < limit:
                        break
                    offset += limit

            except Exception as e:
                print(f"❌ 在 {source} 中按filter获取全部数据失败: {e}")
        return all_items
    


# =======================
# 使用示例
# =======================
if __name__ == "__main__":
    retriever = ICDRetriever(sources="ICD-10-fix", k=40)
    
    
  
    results = retriever.retrieve(
        "血吸虫性肝病",
        #     filter_dict={
        #     "third_chapter":"Q18.1 耳前窦道和囊肿"
        # }
        
    )
    print(results)
    for r in results:
        print(f"  → {r['code']} | {r['name']} | 相似度: {r['similarity']:.3f}")
    
    # # 测试通过code获取item
    # result = retriever.get_by_id("A01.000x0200")
    # print(result)
    
    # # 测试通过过滤条件获取统计数量
    # count = retriever.count({
    #         "$and": [
    #             {"first_chapter": "第1章“某些传染病和寄生虫病”"},
    #             {"second_chapter": "A01 伤寒和副伤寒"},
    #         ]
    #     })
    # print(f"统计数量: {count}")
    
    # # 测试通过过滤条件获取所有item
    # all_items = retriever.get_all_by_filter({
    #         "$and": [
    #             {"first_chapter": "第1章“某些传染病和寄生虫病”"},
    #             {"second_chapter": "A01 伤寒和副伤寒"},
    #             {"third_chapter": "A01.0 伤寒"},
    #         ]
    #     })
    # print(f"获取到 {len(all_items)} 条数据")
    # for item in all_items:
    #     print(f"  → {item['code']} | {item['name']}")
