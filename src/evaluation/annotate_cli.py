import json
import sys
from pathlib import Path

ANNOTATION_FILE = "data/human_annotations.json"

RATING_SCALE = """
Human Quality Score Rating Scale (1 to 5):
  1 = Very Poor   (Irrelevant, rude, contradictory, or unusable)
  2 = Poor        (Major omissions, incorrect details, or poor tone)
  3 = Acceptable  (Addresses main point, minor wording/style gaps)
  4 = Good        (Clear, accurate, polite, and complete)
  5 = Excellent   (Perfectly tailored, flawless tone, highly accurate)
"""

def interactive_annotation(file_path: str = ANNOTATION_FILE):
    path = Path(file_path)
    if not path.exists():
        print(f"Error: {file_path} not found. Run dataset generation first.")
        return

    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    print("=== Human Quality Score Annotation Tool ===")
    print(RATING_SCALE)

    annotated_count = sum(1 for r in records if r.get("human_quality_score") is not None)
    print(f"Current Progress: {annotated_count}/{len(records)} examples annotated.\n")

    modified = False

    for idx, r in enumerate(records, 1):
        if r.get("human_quality_score") is not None:
            continue

        print(f"--- Example [{idx}/{len(records)}] ID: {r['id']} ({r.get('category', 'General')}) ---")
        print(f"INCOMING EMAIL:\n{r['incoming_email']}\n")
        print(f"GENERATED / CANDIDATE REPLY:\n{r['generated_response']}\n")
        print(f"REFERENCE REPLY:\n{r['reference_reply']}\n")

        while True:
            choice = input("Enter Human Rating (1-5, 's' to skip, 'q' to quit & save): ").strip().lower()
            if choice == 'q':
                if modified:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(records, f, indent=2, ensure_ascii=False)
                    print(f"\nSaved changes to {file_path}.")
                print("Exiting annotation tool.")
                return
            elif choice == 's':
                print("Skipped.\n")
                break
            elif choice in ['1', '2', '3', '4', '5']:
                r["human_quality_score"] = int(choice)
                modified = True
                print(f"Recorded score: {choice}/5\n")
                break
            else:
                print("Invalid input. Enter a number between 1 and 5, 's' to skip, or 'q' to quit.")

    if modified:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"\nAll annotations updated and saved to {file_path}.")
        print("You can now run: python -m src.evaluation.human_validation to compute correlation metrics.")

if __name__ == "__main__":
    interactive_annotation()
