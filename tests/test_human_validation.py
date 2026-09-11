import json
import pytest
from pathlib import Path
from src.evaluation.human_validation import (
    seed_annotation_template,
    run_human_validation,
    run_sanity_checks
)

def test_seed_annotation_template(tmp_path):
    target = str(tmp_path / "annotations.json")
    records = seed_annotation_template(
        source_dataset_path="data/processed/train.json",
        target_path=target,
        sample_size=10
    )
    assert len(records) == 10
    assert Path(target).exists()
    assert records[0]["human_quality_score"] is None

def test_unannotated_dataset_reporting(tmp_path):
    target = str(tmp_path / "empty_annotations.json")
    seed_annotation_template(
        source_dataset_path="data/processed/train.json",
        target_path=target,
        sample_size=5
    )
    res = run_human_validation(annotation_file=target)
    assert res["status"] == "pending_annotations"
    assert res["annotated_count"] == 0
    assert "Human validation has not yet been completed" in res["message"]

def test_human_validation_metric_computation(tmp_path):
    target = str(tmp_path / "mock_annotations.json")
    mock_auto = str(tmp_path / "mock_per_response_scores.json")
    mock_data = [
        {
            "id": "HUMAN-0001",
            "incoming_email": "Hi, can we meet Thursday at 2 PM?",
            "generated_response": "Hi, Thursday at 2 PM works fine.",
            "reference_reply": "Hi, Thursday at 2 PM works fine.",
            "human_quality_score": 5  # Converts to 100
        },
        {
            "id": "HUMAN-0002",
            "incoming_email": "Can we meet Thursday at 2 PM?",
            "generated_response": "The weather forecast predicts rain.",
            "reference_reply": "Hi, Thursday at 2 PM works fine.",
            "human_quality_score": 1  # Converts to 0
        }
    ]
    mock_auto_data = [
        {"test_id": "HUMAN-0001", "overall_score": 100.0, "explanation": "Perfect match."},
        {"test_id": "HUMAN-0002", "overall_score": 0.0, "explanation": "Irrelevant response."}
    ]
    with open(target, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=2)
    with open(mock_auto, "w", encoding="utf-8") as f:
        json.dump(mock_auto_data, f, indent=2)

    res = run_human_validation(annotation_file=target, automatic_file=mock_auto)
    assert res["status"] == "completed"
    assert res["annotated_count"] == 2
    assert res["matched_count"] == 2
    assert "metrics" in res
    assert res["metrics"]["pearson_correlation"] == 1.0
    assert res["metrics"]["spearman_correlation"] == 1.0
    assert res["metrics"]["mean_absolute_error"] == 0.0

def test_missing_automatic_score_reporting(tmp_path):
    target = str(tmp_path / "mock_annotations_missing.json")
    mock_auto = str(tmp_path / "mock_per_response_scores_empty.json")
    mock_data = [
        {
            "id": "HUMAN-9999",
            "incoming_email": "Test email",
            "generated_response": "Test reply",
            "reference_reply": "Test reply",
            "human_quality_score": 4
        }
    ]
    with open(target, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=2)
    with open(mock_auto, "w", encoding="utf-8") as f:
        json.dump([], f, indent=2)

    res = run_human_validation(annotation_file=target, automatic_file=mock_auto)
    assert res["status"] == "missing_automatic_scores"
    assert "HUMAN-9999" in res["missing_automatic_ids"]

def test_sanity_checks():
    sanity_results = run_sanity_checks()
    assert len(sanity_results) == 5
    types = [r["type"] for r in sanity_results]
    assert "excellent" in types
    assert "irrelevant" in types
    assert "incomplete" in types
    assert "contradictory" in types
    assert "unprofessional" in types
    
    exc = next(r for r in sanity_results if r["type"] == "excellent")
    irr = next(r for r in sanity_results if r["type"] == "irrelevant")
    assert exc["overall_score"] > irr["overall_score"]
