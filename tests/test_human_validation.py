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
    with open(target, "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=2)

    res = run_human_validation(annotation_file=target)
    assert res["status"] == "completed"
    assert res["annotated_count"] == 2
    assert "metrics" in res
    assert "pearson_correlation" in res["metrics"]
    assert "spearman_correlation" in res["metrics"]
    assert "mean_absolute_error" in res["metrics"]
    assert isinstance(res["metrics"]["mean_absolute_error"], float)

def test_sanity_checks():
    sanity_results = run_sanity_checks()
    assert len(sanity_results) == 5
    types = [r["type"] for r in sanity_results]
    assert "excellent" in types
    assert "irrelevant" in types
    assert "incomplete" in types
    assert "contradictory" in types
    assert "unprofessional" in types
    
    # Excellent score > Irrelevant score
    exc = next(r for r in sanity_results if r["type"] == "excellent")
    irr = next(r for r in sanity_results if r["type"] == "irrelevant")
    assert exc["overall_score"] > irr["overall_score"]
