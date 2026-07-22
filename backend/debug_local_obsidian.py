#!/usr/bin/env python3
"""
Obsidian 集成本地自测脚本
==========================
在你的本地环境直接运行此脚本，可以快速定位：
1. ChromaDB 是否正常工作
2. MiniMax API 是否正常
3. 向量写入是否会超时

使用方法：
    cd backend
    python debug_local_obsidian.py
"""
import os
import sys
import json
import time
import random
import shutil

# 确保能导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SEP = "=" * 60


def _print_env():
    print(SEP)
    print("环境信息")
    print(SEP)
    print(f"Python 版本: {sys.version}")
    print(f"平台: {sys.platform}")

    try:
        import chromadb
        print(f"ChromaDB 版本: {chromadb.__version__}")
    except Exception as e:
        print(f"ChromaDB 导入失败: {e}")

    from app.core.config import settings
    print(f"ChromaDB 持久化目录: {settings.CHROMA_PERSIST_DIR}")
    print(f"Obsidian Vault 路径: {settings.OBSIDIAN_VAULT_PATH}")
    print(f"MiniMax API Key 已配置: {'是' if settings.MINIMAX_API_KEY else '否'}")
    print()


def _test_chromadb_basic():
    """测试1: ChromaDB 基础读写"""
    print(SEP)
    print("测试 1/3: ChromaDB 基础读写（不依赖网络）")
    print(SEP)

    test_dir = os.path.join(os.path.dirname(__file__), "data", "chroma_debug_test")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    try:
        from app.capabilities.rag.vector_store import VectorStore

        vs = VectorStore(persist_dir=test_dir)

        # 写入 5 条测试数据
        docs = [f"Test document {i} content " * 10 for i in range(5)]
        ids = [f"debug_test_{i}" for i in range(5)]
        metas = [{"path": f"test{i}.md", "title": f"Test {i}", "chunk_index": i} for i in range(5)]
        embs = [[random.random() for _ in range(1536)] for _ in range(5)]

        t0 = time.time()
        vs.add_documents("debug_test", docs, ids, metadatas=metas, embeddings=embs)
        elapsed = time.time() - t0

        count = vs.count_documents("debug_test")
        print(f"\n✓ ChromaDB 写入成功: {count} 条, 耗时 {elapsed:.3f}s")

        # 测试搜索
        query_emb = [[random.random() for _ in range(1536)]]
        coll = vs.get_collection("debug_test")
        t0 = time.time()
        results = coll.query(query_embeddings=query_emb, n_results=3)
        print(f"✓ ChromaDB 搜索成功: {len(results['ids'][0])} 条, 耗时 {time.time()-t0:.3f}s")

        vs.delete_collection("debug_test")
        shutil.rmtree(test_dir)
        return True

    except TimeoutError as e:
        print(f"\n✗ ChromaDB 写入超时: {e}")
        print("\n【问题原因】Python 3.13 与 ChromaDB 1.5.9 存在兼容性问题")
        print("【解决方案】")
        print("  1. 降级到 Python 3.10 或 3.11（推荐）")
        print("  2. 或删除 data/chroma 目录后重试")
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        return False
    except Exception as e:
        print(f"\n✗ ChromaDB 测试失败: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        return False


def _test_minimax_api():
    """测试2: MiniMax Embedding API"""
    print("\n" + SEP)
    print("测试 2/3: MiniMax Embedding API（需要网络）")
    print(SEP)

    from app.core.config import settings
    if not settings.MINIMAX_API_KEY:
        print("✗ 跳过: 未配置 MINIMAX_API_KEY")
        return None

    try:
        from app.capabilities.llm.minimax_client import minimax_client

        test_texts = ["这是一段测试文本，用于验证 Embedding API 是否正常工作。"]
        t0 = time.time()
        result = minimax_client.embed(test_texts)
        elapsed = time.time() - t0

        if result and len(result) > 0:
            print(f"✓ MiniMax Embedding API 正常: 返回 {len(result)} 个向量, 维度 {len(result[0])}, 耗时 {elapsed:.3f}s")
            return True
        else:
            print(f"✗ MiniMax Embedding API 返回空结果")
            return False
    except Exception as e:
        print(f"✗ MiniMax Embedding API 失败: {e}")
        return False


def _test_obsidian_reader():
    """测试3: Obsidian Reader 扫描"""
    print("\n" + SEP)
    print("测试 3/3: Obsidian Vault 扫描（不依赖网络）")
    print(SEP)

    try:
        from app.plugins.wechat_writer.obsidian_reader import obsidian_reader

        vault_path = obsidian_reader.vault_path
        print(f"Vault 路径: {vault_path}")
        print(f"Vault 存在: {vault_path.exists()}")

        if not vault_path.exists():
            print("✗ Vault 路径不存在，请检查配置")
            return False

        t0 = time.time()
        files = obsidian_reader.scan_files()
        elapsed = time.time() - t0

        print(f"✓ 扫描完成: {len(files)} 个 Markdown 文件, 耗时 {elapsed:.3f}s")
        if files:
            print(f"  示例文件:")
            for f in files[:3]:
                print(f"    - {f['relative_path']} ({f['size']} bytes)")

        # 测试解析
        if files:
            note = obsidian_reader.parse_note(files[0])
            if note:
                print(f"✓ 笔记解析成功: {note['title']} ({note['word_count']} 字, {len(note['tags'])} 个标签)")
            else:
                print("  笔记解析返回 None（可能是标签不匹配）")

        return True

    except Exception as e:
        print(f"✗ Obsidian Reader 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + SEP)
    print("  Obsidian 集成本地自测工具")
    print(SEP + "\n")

    _print_env()

    results = {}

    results["chromadb"] = _test_chromadb_basic()
    results["minimax"] = _test_minimax_api()
    results["obsidian"] = _test_obsidian_reader()

    print("\n" + SEP)
    print("测试结果汇总")
    print(SEP)
    for name, result in results.items():
        status = "✓ 通过" if result else ("✗ 失败" if result is False else "- 跳过")
        print(f"  {name:12s}: {status}")

    print()
    if results["chromadb"] is False:
        print("【关键问题】ChromaDB 写入失败/超时，这是导致同步卡住的根因。")
        print("         请先解决 ChromaDB 问题（降级 Python 版本）后再测试。")
    elif results["chromadb"] and results["minimax"] and results["obsidian"]:
        print("✓ 所有测试通过！Obsidian 同步应该可以正常工作了。")
        print("  如果仍然有问题，请运行: POST /api/wechat-writer/obsidian/sync?force=true")
    else:
        print("部分测试未通过，请根据上述提示修复。")

    print()


if __name__ == "__main__":
    main()
