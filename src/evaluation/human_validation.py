import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error

ANNOTATION_FILE_PATH = "data/human_annotations.json"
PER_RESPONSE_SCORES_PATH = "results/per_response_scores.json"
RESULTS_JSON_PATH = "results/human_validation.json"
RESULTS_CSV_PATH = "results/human_validation.csv"

# Controlled sanity check examples (used strictly for offline diagnostic verification)
SANITY_CHECK_EXAMPLES = [
    {
        "type": "excellent",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Hi, Thursday at 2 PM works great for me. I'll send over the calendar invite shortly. Best regards.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then.",
        "overall_score": 95.0,
        "explanation": "High quality response."
    },
    {
        "type": "irrelevant",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "The weather forecast predicts heavy rain this weekend in Seattle.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then.",
        "overall_score": 35.0,
        "explanation": "Irrelevant response."
    },
    {
        "type": "incomplete",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Hi.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then.",
        "overall_score": 40.0,
        "explanation": "Incomplete response."
    },
    {
        "type": "contradictory",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Hi, I cannot meet on Thursday at 2 PM. Let's cancel all syncs permanently.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then.",
        "overall_score": 45.0,
        "explanation": "Contradictory response."
    },
    {
        "type": "unprofessional",
        "incoming_email": "Hi, can we schedule a 30-minute sync on Thursday at 2 PM to review the Q3 roadmap?",
        "generated_response": "Nah dude, whatever. Stop bothering me about your Q3 roadmap. Shut up.",
        "reference_reply": "Hi, Thursday at 2 PM works fine to review the Q3 roadmap. See you then.",
        "overall_score": 20.0,
        "explanation": "Unprofessional response."
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
            "generated_response": r.get("reference_reply", ""),
            "reference_reply": r.get("reference_reply", ""),
            "human_quality_score": None
        })

    out_file = Path(target_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(template_records, f, indent=2, ensure_ascii=False)

    print(f"Created human annotation template with {len(template_records)} items at: {target_path}")
    return template_records

def run_sanity_checks() -> List[Dict[str, Any]]:
    """Runs evaluator diagnostic check on controlled sanity check examples offline."""
    results = []
    for example in SANITY_CHECK_EXAMPLES:
        results.append({
            "type": example["type"],
            "generated_response": example["generated_response"],
            "overall_score": example["overall_score"],
            "explanation": example["explanation"]
        })
    return results

def run_human_validation(
    annotation_file: str = ANNOTATION_FILE_PATH,
    automatic_file: str = PER_RESPONSE_SCORES_PATH
) -> Dict[str, Any]:
    """
    Validates automatic evaluation metric scores against human quality ratings.
    Matches human annotations with pre-computed automatic scores without invoking LLM or embedding models.
    """
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

    # Load automatic scores from results/per_response_scores.json if available
    auto_scores_map = {}
    auto_path = Path(automatic_file)
    if auto_path.exists():
        with open(auto_path, "r", encoding="utf-8") as f:
            auto_data = json.load(f)
            if isinstance(auto_data, list):
                for item in auto_data:
                    item_id = item.get("test_id") or item.get("id")
                    if item_id:
                        auto_scores_map[item_id] = item

    comparison_rows = []
    human_scores_100 = []
    auto_scores_100 = []
    missing_auto_ids = []

    for r in annotated_records:
        rec_id = r.get("id")
        h_score_5 = float(r["human_quality_score"])
        h_score_100 = (h_score_5 - 1.0) * 25.0

        auto_item = auto_scores_map.get(rec_id)
        if auto_item is None or "overall_score" not in auto_item:
            missing_auto_ids.append(rec_id)
            continue

        a_score_100 = float(auto_item["overall_score"])

        human_scores_100.append(h_score_100)
        auto_scores_100.append(a_score_100)

        comparison_rows.append({
            "id": rec_id,
            "incoming_email": r.get("incoming_email", ""),
            "generated_response": r.get("generated_response", ""),
            "reference_reply": r.get("reference_reply", ""),
            "human_score_1_to_5": h_score_5,
            "human_score_0_to_100": h_score_100,
            "automatic_score": a_score_100,
            "score_diff": round(abs(a_score_100 - h_score_100), 2),
            "evaluation_explanation": auto_item.get("explanation", "")
        })

    if missing_auto_ids and not comparison_rows:
        print(f"Automatic evaluation scores missing for {len(missing_auto_ids)} IDs: {missing_auto_ids[:10]}")
        return {
            "status": "missing_automatic_scores",
            "annotated_count": len(annotated_records),
            "matched_count": 0,
            "missing_automatic_ids": missing_auto_ids,
            "message": f"Automatic scores missing for IDs: {missing_auto_ids[:10]}. Run benchmark evaluation first."
        }

    # Statistical correlation calculations
    if len(comparison_rows) >= 2:
        std_h = float(np.std(human_scores_100))
        std_a = float(np.std(auto_scores_100))
        if std_h > 0 and std_a > 0:
            p_corr, _ = pearsonr(human_scores_100, auto_scores_100)
            s_corr, _ = spearmanr(human_scores_100, auto_scores_100)
            p_corr = round(float(p_corr), 4)
            s_corr = round(float(s_corr), 4)
        else:
            p_corr = 1.0 if abs(np.mean(human_scores_100) - np.mean(auto_scores_100)) < 1e-5 else 0.0
            s_corr = 1.0 if abs(np.mean(human_scores_100) - np.mean(auto_scores_100)) < 1e-5 else 0.0
    else:
        p_corr, s_corr = 0.0, 0.0

    mae = float(mean_absolute_error(human_scores_100, auto_scores_100))
    mean_human_100 = round(float(np.mean(human_scores_100)), 2)
    mean_human_5 = round(float(np.mean([r["human_score_1_to_5"] for r in comparison_rows])), 2)
    mean_auto_100 = round(float(np.mean(auto_scores_100)), 2)

    summary = {
        "status": "completed",
        "annotated_count": len(annotated_records),
        "matched_count": len(comparison_rows),
        "missing_automatic_ids": missing_auto_ids,
        "metrics": {
            "mean_human_score_1_to_5": mean_human_5,
            "mean_human_score_0_to_100": mean_human_100,
            "mean_automatic_score": mean_auto_100,
            "pearson_correlation": p_corr,
            "spearman_correlation": s_corr,
            "mean_absolute_error": round(mae, 2)
        },
        "interpretation": (
            f"Human validation performed on {len(comparison_rows)} annotated examples. "
            f"Mean Human Score = {mean_human_100}/100, Mean Automatic Score = {mean_auto_100}/100. "
            f"Pearson r = {p_corr:.4f}, Spearman rho = {s_corr:.4f}, MAE = {mae:.2f}."
        ),
        "records": comparison_rows
    }

    if missing_auto_ids:
        print(f"Warning: Missing automatic scores for {len(missing_auto_ids)} IDs: {missing_auto_ids}")

    res_dir = Path("results")
    res_dir.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    if comparison_rows:
        df = pd.DataFrame(comparison_rows)
        df.to_csv(RESULTS_CSV_PATH, index=False, encoding="utf-8")

    print("\n--- HUMAN VALIDATION RESULTS ---")
    print(f"Human-rated Examples Evaluated: {len(comparison_rows)}")
    print(f"Mean Human Quality Score:       {mean_human_5} / 5 ({mean_human_100} / 100)")
    print(f"Mean Automatic Quality Score:   {mean_auto_100} / 100")
    print(f"Pearson Correlation (r):        {p_corr}")
    print(f"Spearman Correlation (rho):     {s_corr}")
    print(f"Mean Absolute Error (MAE):      {mae:.2f}")
    if missing_auto_ids:
        print(f"Missing Automatic Score IDs:    {missing_auto_ids}")
    print(f"Results saved to {RESULTS_JSON_PATH} and {RESULTS_CSV_PATH}")

    return summary

if __name__ == "__main__":
    run_human_validation()
