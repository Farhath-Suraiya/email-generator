import json
from pathlib import Path
from typing import Optional
from src.pipeline.email_pipeline import EmailResponsePipeline

def run_demo(
    test_dataset_path: str = "data/processed/test.json",
    output_dir: str = "results",
    pipeline: Optional[EmailResponsePipeline] = None
) -> dict:
    test_file = Path(test_dataset_path)
    if not test_file.exists():
        raise FileNotFoundError(f"Test dataset not found at {test_dataset_path}")

    with open(test_file, "r", encoding="utf-8") as f:
        test_records = json.load(f)

    if not test_records:
        raise ValueError("Test dataset is empty.")

    # Pick the first record from test dataset
    demo_sample = test_records[0]
    sample_id = demo_sample.get("id", "EML-TEST")
    category = demo_sample.get("category", "General")
    incoming_email = demo_sample["incoming_email"]
    reference_reply = demo_sample["reference_reply"]

    print(f"--- Running End-to-End Pipeline Demo ---")
    print(f"Sample ID: {sample_id} [{category}]")
    print(f"Incoming Email:\n{incoming_email}\n")

    if pipeline is None:
        pipeline = EmailResponsePipeline()

    # Step 1 & 2: Generation (Reference reply NOT passed to prompt)
    # Step 3: Evaluation against reference reply
    pipeline_output = pipeline.process_and_evaluate(
        incoming_email=incoming_email,
        reference_reply=reference_reply
    )

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    results_file = out_path / "demo_result.json"

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(pipeline_output, f, indent=2, ensure_ascii=False)

    print(f"Generated Suggested Reply:\n{pipeline_output['suggested_reply']}\n")
    if pipeline_output.get("evaluation"):
        overall_score = pipeline_output["evaluation"].get("overall_score")
        print(f"Overall Quality Score: {overall_score}/100")
        print(f"Explanation: {pipeline_output['evaluation'].get('overall_explanation')}")

    print(f"\nSaved full demo results to: {results_file}")
    return pipeline_output

if __name__ == "__main__":
    run_demo()
