import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error

from src.evaluation.evaluator import evaluate_response

ANNOTATION_FILE_PATH = "data/human_annotations.json"
RESULTS_JSON_PATH = "results/human_validation.json"
RESULTS_CSV_PATH = "results/human_validation.csv"

# Controlled sanity check examples (used strictly for evaluator diagnostics, not human ground truth)
SANITY_CHECK_EXAMPLES = [
    {
        "type": "excellent",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Hi, Thursday at 2 PM works great for me. I'll send over the calendar invite shortly. Best regards.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then."
    },
    {
        "type": "irrelevant",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "The weather forecast predicts heavy rain this weekend in Seattle.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then."
    },
    {
        "type": "incomplete",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Hi.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then."
    },
    {
        "type": "contradictory",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Hi, I cannot meet on Thursday at 2 PM. Let's cancel all syncs permanently.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then."
    },
    {
        "type": "unprofessional",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Nah dude, whatever. Stop bothering me about your Q3 roadmap. Shut up.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then."
    }
]

def seed_annotation_template(
    source_dataset_path: str = "data/processed/validation.json",
    target_path: str = ANNOTATION_FILE_PATH,
    sample_size: int = 60
) -> List[Dict[str, Any]]:
    """Generate an unannotated human evaluation dataset template."""
    src_file = Path(source_dataset_path)
    if not src_file.exists():
        src_file = Path("data/processed/train.json")

    if not src_file.exists():
        raise FileNotFoundError("Source dataset for annotation template not found.")

    with open(src_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    selected = records[:sample_size]
    template_records = []
    for idx, r in enumerate(selected, 1):
        template_records.append({
            "id": r.get("id", f"HUMAN-{idx:04d}"),
            "category": r.get("category", "General"),
            "incoming_email": r.get("incoming_email", ""),
            "generated_response": r.get("reference_reply", ""),  # Candidate response to evaluate
            "reference_reply": r.get("reference_reply", ""),
            "human_quality_score": None  # Expects integer 1-5 scale from human annotator
        })

    out_file = Path(target_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(template_records, f, indent=2, ensure_ascii=False)

    print(f"Created human annotation template with {len(template_records)} items at: {target_path}")
    return template_records

def run_sanity_checks() -> List[Dict[str, Any]]:
    """Runs evaluator on controlled sanity check examples for diagnostic verification."""
    results = []
    for example in SANITY_CHECK_EXAMPLES:
        eval_res = evaluate_response(
            incoming_email=example["incoming_email"],
            generated_response=example["generated_response"],
            reference_reply=example["reference_reply"]
        )
        results.append({
            "type": example["type"],
            "generated_response": example["generated_response"],
            "overall_score": eval_res["overall_score"],
            "explanation": eval_res["overall_explanation"]
        })
    return results

def run_human_validation(annotation_file: str = ANNOTATION_FILE_PATH) -> Dict[str, Any]:
    ann_path = Path(annotation_file)
    if not ann_path.exists():
        seed_annotation_template(target_path=annotation_file)
        return {
            "status": "pending_annotations",
            "annotated_count": 0,
            "message": f"Annotation template created at {annotation_file}. Human quality scores (1-5 scale) must be filled in before validation can be computed."
        }

    with open(ann_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Filter records that have valid human scores (1-5 scale)
    annotated_records = [
        r for r in records
        if r.get("human_quality_score") is not None
        and isinstance(r.get("human_quality_score"), (int, float))
        and 1 <= r.get("human_quality_score") <= 5
    ]

    if not annotated_records:
        return {
            "status": "pending_annotations",
            "total_records": len(records),
            "annotated_count": 0,
            "message": "Human validation has not yet been completed. Please provide human_quality_score (1-5 scale) for examples in data/human_annotations.json."
        }

    comparison_rows = []
    human_scores_100 = []
    auto_scores_100 = []

    for r in annotated_records:
        h_score_5 = float(r["human_quality_score"])
        # Convert 1-5 scale to 0-100 scale (1 -> 0, 5 -> 100)
        h_score_100 = (h_score_5 - 1.0) * 25.0

        eval_res = evaluate_response(
            incoming_email=r["incoming_email"],
            generated_response=r["generated_response"],
            reference_reply=r["reference_reply"]
        )
        a_score_100 = float(eval_res["overall_score"])

        human_scores_100.append(h_score_100)
        auto_scores_100.append(a_score_100)

        comparison_rows.append({
            "id": r.get("id"),
            "incoming_email": r["incoming_email"],
            "generated_response": r["generated_response"],
            "reference_reply": r["reference_reply"],
            "human_score_1_to_5": h_score_5,
            "human_score_0_to_100": h_score_100,
            "automatic_score": a_score_100,
            "score_diff": round(abs(a_score_100 - h_score_100), 2),
            "evaluation_explanation": eval_res.get("overall_explanation")
        })

    # Statistical correlation calculations
    if len(annotated_records) >= 2:
        p_corr, _ = pearsonr(human_scores_100, auto_scores_100)
        s_corr, _ = spearmanr(human_scores_100, auto_scores_100)
    else:
        p_corr, s_corr = 0.0, 0.0

    mae = float(mean_absolute_error(human_scores_100, auto_scores_100))

    summary = {
        "status": "completed",
        "annotated_count": len(annotated_records),
        "metrics": {
            "pearson_correlation": round(float(p_corr), 4),
            "spearman_correlation": round(float(s_corr), 4),
            "mean_absolute_error": round(mae, 2)
        },
        "interpretation": f"Human validation performed on {len(annotated_records)} annotated examples. Pearson r = {p_corr:.4f}, Spearman rho = {s_corr:.4f}, MAE = {mae:.2f}.",
        "records": comparison_rows
    }

    # Save output JSON and CSV
    res_dir = Path("results")
    res_dir.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    df = pd.DataFrame(comparison_rows)
    df.to_csv(RESULTS_CSV_PATH, index=False, encoding="utf-8")

    print(f"Validation metrics saved to {RESULTS_JSON_PATH} and {RESULTS_CSV_PATH}")
    return summary

if __name__ == "__main__":
    run_human_validation()
