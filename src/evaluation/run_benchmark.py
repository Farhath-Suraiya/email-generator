import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from src.pipeline.email_pipeline import EmailResponsePipeline

PER_RESPONSE_JSON = "results/per_response_scores.json"
PER_RESPONSE_CSV = "results/per_response_scores.csv"
REPORT_JSON = "results/evaluation_report.json"
REPORT_MD = "results/evaluation_report.md"

def run_benchmark(
    test_path: str = "data/processed/test.json",
    output_dir: str = "results",
    limit: Optional[int] = None,
    pipeline: Optional[EmailResponsePipeline] = None,
    delay_between_requests: float = 1.0
) -> Dict[str, Any]:
    test_file = Path(test_path)
    if not test_file.exists():
        raise FileNotFoundError(f"Test dataset file not found at {test_path}")

    with open(test_file, "r", encoding="utf-8") as f:
        test_records = json.load(f)

    if not test_records:
        raise ValueError("Test dataset is empty.")

    if limit is not None and limit > 0:
        test_records = test_records[:limit]

    if pipeline is None:
        pipeline = EmailResponsePipeline()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    per_response_results = []
    
    print(f"--- Running Benchmark Evaluation on {len(test_records)} Test Samples ---")

    for idx, item in enumerate(test_records, 1):
        test_id = item.get("id", f"TEST-{idx:04d}")
        category = item.get("category", "General")
        incoming_email = item["incoming_email"]
        reference_reply = item["reference_reply"]

        print(f"[{idx}/{len(test_records)}] Processing sample {test_id} [{category}]...")

        try:
            # Step 1: Generate response WITHOUT reference reply
            # Step 2: Evaluate AFTER generation
            pipeline_output = pipeline.process_and_evaluate(
                incoming_email=incoming_email,
                reference_reply=reference_reply
            )
        except Exception as e:
            print(f"Error evaluating sample {test_id}: {str(e)}")
            raise e

        eval_data = pipeline_output.get("evaluation", {})
        gen_reply = pipeline_output.get("suggested_reply", "")

        sem_score = float(eval_data.get("semantic_similarity", {}).get("score", 0.0))
        rel_score = float(eval_data.get("relevance", {}).get("score", 0.0))
        comp_score = float(eval_data.get("completeness", {}).get("score", 0.0))
        tone_score = float(eval_data.get("tone", {}).get("score", 0.0))
        fact_score = float(eval_data.get("factual_consistency", {}).get("score", 0.0))
        overall_score = float(eval_data.get("overall_score", 0.0))

        record_res = {
            "test_id": test_id,
            "category": category,
            "incoming_email": incoming_email,
            "generated_response": gen_reply,
            "reference_reply": reference_reply,
            "semantic_score": sem_score,
            "relevance_score": rel_score,
            "completeness_score": comp_score,
            "tone_score": tone_score,
            "factual_consistency_score": fact_score,
            "overall_score": overall_score,
            "explanation": eval_data.get("overall_explanation", ""),
            "strengths": eval_data.get("strengths", []),
            "issues": eval_data.get("issues", [])
        }
        per_response_results.append(record_res)
        
        if delay_between_requests > 0 and idx < len(test_records):
            time.sleep(delay_between_requests)

    # Save per-response JSON and CSV
    per_json_path = out_dir / "per_response_scores.json"
    per_csv_path = out_dir / "per_response_scores.csv"

    with open(per_json_path, "w", encoding="utf-8") as f:
        json.dump(per_response_results, f, indent=2, ensure_ascii=False)

    df_per = pd.DataFrame([
        {
            **r,
            "strengths": "; ".join(r["strengths"]),
            "issues": "; ".join(r["issues"])
        }
        for r in per_response_results
    ])
    df_per.to_csv(per_csv_path, index=False, encoding="utf-8")

    # Compute overall benchmark statistics
    n_samples = len(per_response_results)
    avg_sem = round(float(np.mean([r["semantic_score"] for r in per_response_results])), 2)
    avg_rel = round(float(np.mean([r["relevance_score"] for r in per_response_results])), 2)
    avg_comp = round(float(np.mean([r["completeness_score"] for r in per_response_results])), 2)
    avg_tone = round(float(np.mean([r["tone_score"] for r in per_response_results])), 2)
    avg_fact = round(float(np.mean([r["factual_consistency_score"] for r in per_response_results])), 2)
    avg_overall = round(float(np.mean([r["overall_score"] for r in per_response_results])), 2)

    all_scores = [r["overall_score"] for r in per_response_results]
    score_dist = {
        "mean": avg_overall,
        "std": round(float(np.std(all_scores)), 2),
        "min": round(float(np.min(all_scores)), 2),
        "max": round(float(np.max(all_scores)), 2),
        "range_90_100": sum(1 for s in all_scores if 90 <= s <= 100),
        "range_70_89": sum(1 for s in all_scores if 70 <= s < 90),
        "range_50_69": sum(1 for s in all_scores if 50 <= s < 70),
        "range_below_50": sum(1 for s in all_scores if s < 50)
    }

    # Category-wise averages
    df_cat = pd.DataFrame(per_response_results)
    cat_summary = {}
    for cat, group in df_cat.groupby("category"):
        cat_summary[cat] = {
            "count": len(group),
            "avg_overall_score": round(float(group["overall_score"].mean()), 2),
            "avg_relevance": round(float(group["relevance_score"].mean()), 2),
            "avg_completeness": round(float(group["completeness_score"].mean()), 2),
            "avg_tone": round(float(group["tone_score"].mean()), 2),
            "avg_factuality": round(float(group["factual_consistency_score"].mean()), 2)
        }

    # Strongest and Weakest examples
    sorted_by_score = sorted(per_response_results, key=lambda x: x["overall_score"], reverse=True)
    strongest = sorted_by_score[:3]
    weakest = sorted_by_score[-3:]

    # Common failure patterns
    issue_counts = {}
    for r in per_response_results:
        for issue in r["issues"]:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

    sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
    common_failures = [{"issue": k, "frequency": v} for k, v in sorted_issues]

    report_data = {
        "number_of_test_emails": n_samples,
        "overall_quality_score": avg_overall,
        "average_dimension_scores": {
            "semantic_similarity": avg_sem,
            "relevance": avg_rel,
            "completeness": avg_comp,
            "professional_tone": avg_tone,
            "factual_consistency": avg_fact
        },
        "score_distribution": score_dist,
        "category_wise_scores": cat_summary,
        "strongest_examples": strongest,
        "weakest_examples": weakest,
        "common_failure_patterns": common_failures
    }

    report_json_path = out_dir / "evaluation_report.json"
    report_md_path = out_dir / "evaluation_report.md"

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    # Generate markdown report
    md_content = f"""# AI Email Suggested-Response System — Evaluation Report

## Benchmark Overview
- **Number of Test Emails Evaluated:** {n_samples}
- **Overall Response Quality Score:** **{avg_overall} / 100**

## Average Dimension Quality Scores
| Dimension | Weight | Average Score (0-100) |
| :--- | :---: | :---: |
| **Semantic Similarity** | 25% | {avg_sem} |
| **Relevance** | 20% | {avg_rel} |
| **Completeness** | 20% | {avg_comp} |
| **Professional Tone** | 15% | {avg_tone} |
| **Factual Consistency** | 20% | {avg_fact} |

## Quality Score Distribution
- **Mean Score:** {score_dist['mean']}
- **Std Dev:** {score_dist['std']}
- **Min / Max:** {score_dist['min']} / {score_dist['max']}
- **Score Brackets:**
  - Excellent [90-100]: {score_dist['range_90_100']} emails
  - Good [70-89]: {score_dist['range_70_89']} emails
  - Moderate [50-69]: {score_dist['range_50_69']} emails
  - Poor [<50]: {score_dist['range_below_50']} emails

## Category-wise Quality Breakdown
| Category | Samples | Avg Quality Score | Relevance | Completeness | Tone | Factuality |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for cat, stats in cat_summary.items():
        md_content += f"| {cat} | {stats['count']} | {stats['avg_overall_score']} | {stats['avg_relevance']} | {stats['avg_completeness']} | {stats['avg_tone']} | {stats['avg_factuality']} |\n"

    md_content += "\n## Common Failure Patterns\n"
    if common_failures:
        for fail in common_failures[:5]:
            md_content += f"- **{fail['issue']}**: {fail['frequency']} occurrences\n"
    else:
        md_content += "No recurring failure patterns detected.\n"

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nBenchmark evaluation complete! Reports saved to {report_json_path} and {report_md_path}")
    return report_data

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run benchmark evaluation on test dataset.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of test samples to evaluate")
    args = parser.parse_args()
    run_benchmark(limit=args.limit)

