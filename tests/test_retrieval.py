import os
from pathlib import Path
import pytest
from src.retrieval.index import FAISSIndexManager
from src.retrieval.retriever import EmailRetriever, retrieve_similar_emails

def test_faiss_index_creation_and_retrieval(tmp_path):
    index_dir = str(tmp_path / "test_index")
    
    # 1. Build index from train.json
    manager = FAISSIndexManager(index_dir=index_dir)
    count = manager.build_index(train_path="data/processed/train.json")
    
    assert count > 0
    assert Path(index_dir, "faiss_index.bin").exists()
    assert Path(index_dir, "metadata.json").exists()

    # 2. Test retriever
    retriever = EmailRetriever(index_dir=index_dir)
    query = "Hi, can we schedule a meeting on Thursday to discuss the roadmap?"
    results = retriever.retrieve_similar_emails(query, top_k=3)

    # 3. Assertions
    assert len(results) == 3
    for res in results:
        assert "id" in res
        assert "category" in res
        assert "incoming_email" in res
        assert "reference_reply" in res
        assert "score" in res
        assert isinstance(res["score"], float)
        assert res["incoming_email"] != ""
        assert res["reference_reply"] != ""

def test_standalone_retrieve_similar_emails():
    query = "Invoice payment confirmation"
    results = retrieve_similar_emails(email=query, top_k=2)
    assert len(results) == 2
    assert "incoming_email" in results[0]
    assert "reference_reply" in results[0]
    assert "score" in results[0]
