import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.evaluation.run_benchmark import run_benchmark
from src.pipeline.email_pipeline import EmailResponsePipeline
from src.generation.llm import LLMClient

def test_benchmark_execution_and_reporting(tmp_path):
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Hi Bob, Thursday at 2 PM works fine. Thanks, Alice."
    pipeline = EmailResponsePipeline(llm_client=mock_llm)

    out_dir = str(tmp_path / "results")
    report = run_benchmark(
        test_path="data/processed/test.json",
        output_dir=out_dir,
        limit=5,
        pipeline=pipeline
    )

    assert report["number_of_test_emails"] == 5
    assert "overall_quality_score" in report
    assert "average_dimension_scores" in report
    assert "score_distribution" in report
    assert "category_wise_scores" in report

    # Verify generated output files exist
    assert Path(out_dir, "per_response_scores.json").exists()
    assert Path(out_dir, "per_response_scores.csv").exists()
    assert Path(out_dir, "evaluation_report.json").exists()
    assert Path(out_dir, "evaluation_report.md").exists()

    # Verify terminology in report markdown
    with open(Path(out_dir, "evaluation_report.md"), "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "Overall Response Quality Score" in md_text
    assert "classification accuracy" not in md_text.lower()

    # Verify per response JSON schema
    with open(Path(out_dir, "per_response_scores.json"), "r", encoding="utf-8") as f:
        per_resp = json.load(f)

    assert len(per_resp) == 5
    item = per_resp[0]
    required_keys = [
        "test_id", "category", "incoming_email", "generated_response",
        "reference_reply", "semantic_score", "relevance_score",
        "completeness_score", "tone_score", "factual_consistency_score",
        "overall_score", "explanation", "strengths", "issues"
    ]
    for key in required_keys:
        assert key in item

def test_benchmark_no_reference_reply_leakage(tmp_path):
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate.return_value = "Mock response"
    pipeline = EmailResponsePipeline(llm_client=mock_llm)

    run_benchmark(
        test_path="data/processed/test.json",
        output_dir=str(tmp_path),
        limit=2,
        pipeline=pipeline
    )

    # Inspect generation calls to LLM
    assert mock_llm.generate.called
    for call in mock_llm.generate.call_args_list:
        user_prompt = call[1].get("user_prompt", "") or call[0][1]
        # Ensure system instruction/prompt passed during generation phase doesn't contain reference reply section title
        if "HISTORICAL REFERENCE EXAMPLES:" in user_prompt:
            assert "HIDDEN REFERENCE REPLY" not in user_prompt
