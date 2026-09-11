import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.pipeline.email_pipeline import EmailResponsePipeline
from src.generation.llm import LLMClient
from src.pipeline.run_demo import run_demo

def test_retrieval_does_not_index_test_dataset():
    """Verify FAISS retrieval returns only training dataset examples, never test dataset IDs."""
    test_path = Path("data/processed/test.json")
    train_path = Path("data/processed/train.json")
    
    assert test_path.exists() and train_path.exists()
    
    with open(test_path, "r", encoding="utf-8") as f:
        test_ids = set(r["id"] for r in json.load(f))
        
    with open(train_path, "r", encoding="utf-8") as f:
        train_ids = set(r["id"] for r in json.load(f))
        
    # Ensure train and test are disjoint
    assert len(train_ids.intersection(test_ids)) == 0

    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Mocked LLM reply for testing."

    pipeline = EmailResponsePipeline(llm_client=mock_llm)
    sample_query = "Can we set up a quick 30-minute sync regarding Q3 roadmap?"
    res = pipeline.generate_response(sample_query, top_k=3)
    
    retrieved_ids = [ex["id"] for ex in res["retrieved_examples"]]
    for r_id in retrieved_ids:
        assert r_id in train_ids, f"Retrieved item {r_id} was found in train dataset"
        assert r_id not in test_ids, f"Data leakage error: Retrieved item {r_id} was from test dataset!"

def test_mode_a_generation_only():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Hello, Thursday at 10 AM works great for me."
    
    pipeline = EmailResponsePipeline(llm_client=mock_llm)
    res = pipeline.process_email("Hi, are you free Thursday at 10 AM?")
    
    assert res["incoming_email"] == "Hi, are you free Thursday at 10 AM?"
    assert res["suggested_reply"] == "Hello, Thursday at 10 AM works great for me."
    assert len(res["retrieved_examples"]) == 3
    assert res.get("evaluation") is None
    assert "reference_reply" not in res

def test_reference_reply_not_passed_to_llm_generation_prompt():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Sure, Friday works."
    
    pipeline = EmailResponsePipeline(llm_client=mock_llm)
    secret_ref = "SECRET_REFERENCE_REPLY_12345"
    
    pipeline.process_and_evaluate(
        incoming_email="Hi, free on Friday?",
        reference_reply=secret_ref
    )
    
    # Verify first call to LLM (Generation call) does NOT contain secret reference reply
    assert mock_llm.generate.called
    first_call_args = mock_llm.generate.call_args_list[0]
    gen_user_prompt = first_call_args[1].get("user_prompt", "") or first_call_args[0][1]
    
    assert secret_ref not in gen_user_prompt, "Data leakage: reference reply was passed to LLM generation prompt!"

def test_mode_b_generation_and_evaluation():
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Hi Bob, I confirm receipt of invoice #101. Thanks, Alice."
    
    pipeline = EmailResponsePipeline(llm_client=mock_llm)
    res = pipeline.process_email(
        incoming_email="Hi Alice, please confirm receipt of invoice #101.",
        reference_reply="Hi Bob, invoice #101 has been received."
    )
    
    assert res["incoming_email"] == "Hi Alice, please confirm receipt of invoice #101."
    assert res["reference_reply"] == "Hi Bob, invoice #101 has been received."
    assert res["suggested_reply"] == "Hi Bob, I confirm receipt of invoice #101. Thanks, Alice."
    assert "evaluation" in res and res["evaluation"] is not None
    assert "overall_score" in res["evaluation"]
    assert res["evaluation"]["overall_score"] >= 0.0

def test_run_demo_execution(tmp_path):
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Thanks for the update. We will adjust our plan."
    pipeline = EmailResponsePipeline(llm_client=mock_llm)

    demo_out = run_demo(
        test_dataset_path="data/processed/test.json",
        output_dir=str(tmp_path),
        pipeline=pipeline
    )
    assert "incoming_email" in demo_out
    assert "suggested_reply" in demo_out
    assert "evaluation" in demo_out
    assert (tmp_path / "demo_result.json").exists()
