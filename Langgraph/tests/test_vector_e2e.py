import importlib.util
import sys

def load_module_direct(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

# 直接加载，不触发 infra/__init__.py 和 protocols/__init__.py 的全量导入
vs_proto = load_module_direct("protocols.vector_store", "protocols/vector_store.py")
embed_mod = load_module_direct("infra.vector.local_embedder", "infra/vector/local_embedder.py")
qdrant_mod = load_module_direct("infra.vector.qdrant_store", "infra/vector/qdrant_store.py")

LocalSentenceEmbedder = embed_mod.LocalSentenceEmbedder
QdrantVectorStore = qdrant_mod.QdrantVectorStore
VectorDocument = vs_proto.VectorDocument


def run_e2e_smoke_test():
    test_db_path = "./tmp_qdrant_e2e"
    collection = "test_ci_wiki"

    try:
        # 1. 初始化基础设施实现 (验证开源模型下载/加载 + 本地 Qdrant 初始化)
        print("1. 正在加载开源向量模型...")
        embedder = LocalSentenceEmbedder(model_name="BAAI/bge-small-zh-v1.5", device="cpu")
        store = QdrantVectorStore(path=test_db_path)
        store.ensure_collection(collection_name=collection, dimension=embedder.dimension)

        # 2. 模拟你 20-wiki 的分层数据 (包含 gold/debug 隔离、degree 权重、双链信息)
        mock_docs = [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "text": "当上游 CI 流水线触发频率过高时，通过令牌桶限流与队列背压控制防止下游构建节点 OOM 超时。",
                "payload": {
                    "stage": "gold",
                    "layer": "labeling",
                    "domain": "ci",
                    "degree": 0.92,
                    "file_path": "20_wiki/gold/labeling/lbl_backpressure.md",
                    "wikilinks": ["rel_cardinality_refines_backpressure", "info_ci_runner_config"]
                }
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "text": "【实验草稿】流水线并发超时可能与 Docker 镜像拉取慢有关，待验证。",
                "payload": {
                    "stage": "debug",  # 未验证的 debug 数据，检索时应该被过滤掉
                    "layer": "labeling",
                    "domain": "ci",
                    "degree": 0.50,
                    "file_path": "20_wiki/debug/labeling/lbl_draft.md",
                    "wikilinks": []
                }
            }
        ]

        # 3. 批量向量化并入库 (Upsert)
        print("2. 正在生成向量并写入 Qdrant...")
        texts = [d["text"] for d in mock_docs]
        vectors = embedder.embed_batch(texts)
        
        vector_docs = [
            VectorDocument(id=d["id"], text=d["text"], vector=vec, payload=d["payload"])
            for d, vec in zip(mock_docs, vectors)
        ]
        store.upsert(collection_name=collection, documents=vector_docs)

        # 4. 模拟用户提问 + 5.2 元数据前置硬过滤
        user_query = "构建任务发太快把下游打挂了怎么限流？"  # 故意不提“背压”二字，测试语义理解
        print(f"3. 模拟用户提问: '{user_query}'")
        query_vec = embedder.embed_text(user_query)

        hits = store.search(
            collection_name=collection,
            query_vector=query_vec,
            filters={
                "stage": ["gold", "release"],  # 测试列表过滤 (IN)
                "layer": "labeling",           # 测试精确过滤 (=)
                "degree": {"$gte": 0.8}        # 测试数值范围过滤 (>=)
            },
            top_k=2
        )

        # 5. 验证结果
        print("\n--- 检索结果 ---")
        assert len(hits) == 1, f"预期只命中 1 条 gold 数据，实际命中 {len(hits)} 条"
        hit = hits[0]
        print(f"✅ 命中分数: {hit.score:.4f}")
        print(f"✅ 命中文本: {hit.payload['_text']}")
        print(f"✅ 关联双链: {hit.payload['wikilinks']}")
        print("🎉 基础设施层端到端测试完美通过！")

    finally:
        # 清理临时测试目录
        if Path(test_db_path).exists():
            shutil.rmtree(test_db_path, ignore_errors=True)

if __name__ == "__main__":
    run_e2e_smoke_test()
