# insert.py
import json
import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from config import DATA_FILES, VECTORSTORE_ROOT, EMBEDDING_API_URL, EMBEDDING_MODEL_NAME
from tqdm import tqdm

# 全局共享嵌入模型
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


def count_lines(file_path: str):
    """快速统计文件行数（用于 tqdm 进度条）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)


def read_docs_from_file(file_path: str, source: str):
    """生成器：逐行读取文件，返回 Document"""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if "code" not in item or "name" not in item:
                    continue

                metadata = {
                    "source": source,
                    **item
                }

                yield Document(
                    page_content=item["name"],
                    metadata=metadata
                )
            except json.JSONDecodeError:
                continue


def upsert_source(source: str, file_path: str, batch_size=1):
    """
    插入或更新 source
    ⚠️ 关键修改：默认 batch_size=1 以避免服务端并发乱序
    """
    persist_dir = os.path.join(VECTORSTORE_ROOT, source)
    os.makedirs(VECTORSTORE_ROOT, exist_ok=True)

    try:
        total_lines = count_lines(file_path)
    except:
        total_lines = 30000

    # 初始化向量库
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=get_embeddings(),
        collection_metadata={"hnsw:space": "cosine"}
    )

    new_docs_buffer = []
    new_ids_buffer = []  # 👈 新增：用于存储 ID
    inserted_count = 0

    print(f"🚀 开始处理 {source}，强制模式 batch_size={batch_size}...")

    with tqdm(
        total=total_lines,
        desc=f"📝 {source}",
        unit="条",
        ncols=100
    ) as pbar:

        for doc in read_docs_from_file(file_path, source):
            # 获取唯一 ID (使用 code)
            doc_id = doc.metadata["code"]

            new_docs_buffer.append(doc)
            new_ids_buffer.append(doc_id)

            # 缓冲区满（这里通常是 1）则写入
            if len(new_docs_buffer) >= batch_size:
                # ✅ 显式传入 ids，确保数据一一对应，且支持更新覆盖
                vectorstore.add_documents(new_docs_buffer, ids=new_ids_buffer)
                
                inserted_count += len(new_docs_buffer)
                new_docs_buffer.clear()
                new_ids_buffer.clear()
                pbar.set_postfix({"inserted": inserted_count})
            
            pbar.update(1)

        # 处理剩余数据
        if new_docs_buffer:
            vectorstore.add_documents(new_docs_buffer, ids=new_ids_buffer)
            inserted_count += len(new_docs_buffer)

    # ❌ 已删除 vectorstore.persist()，Chroma 新版会自动保存
    tqdm.write(f"✅ {source}: 完成！共处理 {inserted_count} 条 → {persist_dir}")


def batch_upsert(batch_size=1):
    """批量处理所有 source，强制 batch_size=1"""
    for source, file_path in DATA_FILES.items():
        try:
            upsert_source(source, file_path, batch_size=batch_size)
        except Exception as e:
            tqdm.write(f"❌ {source} 失败: {e}")


def test_query(source: str, query: str, k: int = 5, filter_dict: dict = None):
    """查询测试"""
    persist_dir = os.path.join(VECTORSTORE_ROOT, source)
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=get_embeddings(),
        collection_metadata={"hnsw:space": "cosine"}
    )

    print(f"\n🔍 查询: '{query}'")
    if filter_dict:
        print(f"FilterWhere: {filter_dict}")
    
    try:
        docs_and_scores = vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter=filter_dict
        )

        for i, (doc, score) in enumerate(docs_and_scores, 1):
            meta = doc.metadata
            print(f"\n{i}. 相似度: {1 - score:.4f}") # Chroma返回的是距离，1-距离=相似度
            print(f"   名称: {meta.get('name', 'N/A')}")
            print(f"   编码: {meta.get('code', 'N/A')}")
            print(f"   ID: {doc.metadata.get('code')}") # 验证ID是否正确
    except Exception as e:
        print(f"查询失败 (可能是库为空): {e}")


if __name__ == "__main__":
    # ⚠️ 关键：这里必须设为 1，解决 vLLM 乱序问题
    batch_upsert(batch_size=1)

    print("\n" + "="*60 + "\n")
    
    # 🔍 验证修复效果
    test_query("ICD-10-fix", "先天性耳前瘘管", k=5)